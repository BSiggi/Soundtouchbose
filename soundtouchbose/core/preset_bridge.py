"""Best-effort preset bridge inference and playback control."""

from __future__ import annotations

import logging
import time
from collections import deque
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable

from soundtouchbose.api.client import SoundTouchClient, SoundTouchRequestError
from soundtouchbose.core.config import ConfigStore
from soundtouchbose.core.error_texts import user_error_text
from soundtouchbose.core.preset_manager import PresetManager

LOGGER = logging.getLogger(__name__)
HARDWARE_PRESET_CACHE_TTL_SECONDS = 300


@dataclass(slots=True)
class _PresetSignature:
    source: str
    location: str
    name: str


class PresetBridgeController:
    """Infer preset key triggers and launch local app mapping for that preset."""

    def __init__(
        self,
        config_store: ConfigStore,
        preset_manager: PresetManager,
        client_factory: Callable[[str], SoundTouchClient],
    ) -> None:
        self.config_store = config_store
        self.preset_manager = preset_manager
        self.client_factory = client_factory
        self._hardware_presets: dict[str, dict[int, _PresetSignature]] = {}
        self._hardware_presets_loaded_at: dict[str, float] = {}
        self._last_inferred_preset: dict[str, int | None] = {}
        self._device_status: dict[str, dict[str, Any]] = {}
        self._recent_events: deque[dict[str, Any]] = deque(maxlen=100)

    def is_enabled(self) -> bool:
        return bool(self.config_store.load_settings().get("preset_bridge_enabled", False))

    def get_device_status(self, ip_address: str) -> dict[str, Any]:
        return deepcopy(self._ensure_device_status(ip_address))

    def diagnostics_snapshot(self) -> dict[str, Any]:
        mappings = self.preset_manager.load_bridge_mappings()
        known_ips = sorted(set(mappings) | set(self._device_status))
        return {
            "enabled": self.is_enabled(),
            "devices": {ip_address: self.get_device_status(ip_address) for ip_address in known_ips},
            "recent_events": list(self._recent_events),
        }

    def handle_snapshot(self, ip_address: str, snapshot: dict[str, Any]) -> None:
        status = self._ensure_device_status(ip_address)
        status["bridge_enabled"] = self.is_enabled()
        status["last_snapshot"] = self._snapshot_summary(snapshot)
        if not status["bridge_enabled"]:
            status["last_launch"] = {
                "attempted": False,
                "result": "bridge_disabled",
                "station_name": "",
                "error": "",
                "observed_at": self._timestamp(),
            }
            return
        preset_number, trigger_mode = self._infer_preset_number(ip_address, snapshot)
        if preset_number is None:
            self._last_inferred_preset[ip_address] = None
            status["last_trigger"] = {
                "detected": False,
                "preset_number": None,
                "mode": None,
                "observed_at": self._timestamp(),
            }
            return
        if self._last_inferred_preset.get(ip_address) == preset_number:
            return
        self._last_inferred_preset[ip_address] = preset_number
        status["last_trigger"] = {
            "detected": True,
            "preset_number": preset_number,
            "mode": trigger_mode,
            "observed_at": self._timestamp(),
        }
        station = self.preset_manager.get_bridge_station(ip_address, preset_number)
        if not station:
            LOGGER.info(
                "Preset bridge enabled but no local mapping for device=%s preset=%s",
                ip_address,
                preset_number,
            )
            status["last_launch"] = {
                "attempted": False,
                "result": "no_mapping",
                "station_name": "",
                "error": "",
                "observed_at": self._timestamp(),
            }
            self._record_event(
                ip_address,
                preset_number=preset_number,
                trigger_mode=trigger_mode or "unknown",
                station_name="",
                attempted=False,
                result="no_mapping",
            )
            return
        try:
            self.client_factory(ip_address).select(station)
        except SoundTouchRequestError as exc:
            error_text = user_error_text(exc)
            status["last_launch"] = {
                "attempted": True,
                "result": "failed",
                "station_name": station.name,
                "error": error_text,
                "endpoint": exc.endpoint,
                "status_code": exc.status_code,
                "observed_at": self._timestamp(),
            }
            self._record_event(
                ip_address,
                preset_number=preset_number,
                trigger_mode=trigger_mode or "unknown",
                station_name=station.name,
                attempted=True,
                result="failed",
                error=error_text,
            )
            LOGGER.warning(
                "Preset bridge launch failed device=%s preset=%s station=%s endpoint=%s status=%s",
                ip_address,
                preset_number,
                station.name,
                exc.endpoint,
                exc.status_code,
            )
            return
        status["last_launch"] = {
            "attempted": True,
            "result": "succeeded",
            "station_name": station.name,
            "error": "",
            "observed_at": self._timestamp(),
        }
        self._record_event(
            ip_address,
            preset_number=preset_number,
            trigger_mode=trigger_mode or "unknown",
            station_name=station.name,
            attempted=True,
            result="succeeded",
        )
        LOGGER.info(
            "Preset bridge launch succeeded device=%s preset=%s station=%s source=%s endpoint=/select status=200",
            ip_address,
            preset_number,
            station.name,
            station.source,
        )

    def _infer_preset_number(self, ip_address: str, snapshot: dict[str, Any]) -> tuple[int | None, str | None]:
        preset_id = snapshot.get("preset_id")
        if isinstance(preset_id, int) and 1 <= preset_id <= 6:
            LOGGER.info(
                "Preset bridge trigger detected device=%s preset=%s mode=direct",
                ip_address,
                preset_id,
            )
            return preset_id, "direct"
        match = self._match_from_hardware_cache(ip_address, snapshot)
        if match is not None:
            LOGGER.info(
                "Preset bridge trigger inferred device=%s preset=%s mode=now_playing_signature",
                ip_address,
                match,
            )
            return match, "now_playing_signature"
        return None, None

    def _match_from_hardware_cache(self, ip_address: str, snapshot: dict[str, Any]) -> int | None:
        signatures = self._hardware_preset_signatures(ip_address)
        if not signatures:
            return None
        content_item = snapshot.get("content_item") if isinstance(snapshot.get("content_item"), dict) else {}
        source = str((content_item or {}).get("source") or snapshot.get("source") or "").strip()
        location = str((content_item or {}).get("location") or "").strip()
        item_name = str(snapshot.get("item_name") or snapshot.get("station_name") or "").strip()
        if not source and not location and not item_name:
            return None
        for preset_number, signature in signatures.items():
            if location and signature.location and location == signature.location:
                return preset_number
            if source and item_name and source == signature.source and item_name == signature.name:
                return preset_number
        return None

    def _hardware_preset_signatures(self, ip_address: str) -> dict[int, _PresetSignature]:
        last_loaded = self._hardware_presets_loaded_at.get(ip_address, 0.0)
        if ip_address in self._hardware_presets and time.time() - last_loaded < HARDWARE_PRESET_CACHE_TTL_SECONDS:
            return self._hardware_presets[ip_address]
        try:
            presets = self.client_factory(ip_address).get_presets()
        except Exception:
            return self._hardware_presets.get(ip_address, {})
        signatures: dict[int, _PresetSignature] = {}
        for item in presets:
            try:
                preset_number = int(item.get("id", 0))
            except (TypeError, ValueError):
                continue
            if not 1 <= preset_number <= 6:
                continue
            signatures[preset_number] = _PresetSignature(
                source=str(item.get("source", "")).strip(),
                location=str(item.get("location", "")).strip(),
                name=str(item.get("name", "")).strip(),
            )
        self._hardware_presets[ip_address] = signatures
        self._hardware_presets_loaded_at[ip_address] = time.time()
        return signatures

    def _ensure_device_status(self, ip_address: str) -> dict[str, Any]:
        status = self._device_status.setdefault(
            ip_address,
            {
                "bridge_enabled": self.is_enabled(),
                "mappings_loaded": False,
                "mapping_count": 0,
                "mapped_presets": [],
                "last_snapshot": {},
                "last_trigger": {
                    "detected": False,
                    "preset_number": None,
                    "mode": None,
                    "observed_at": None,
                },
                "last_launch": {
                    "attempted": False,
                    "result": "idle",
                    "station_name": "",
                    "error": "",
                    "observed_at": None,
                },
            },
        )
        mappings = self.preset_manager.get_bridge_mappings(ip_address)
        status["bridge_enabled"] = self.is_enabled()
        status["mapping_count"] = len(mappings)
        status["mappings_loaded"] = bool(mappings)
        status["mapped_presets"] = sorted(
            int(preset_number)
            for preset_number in mappings
            if str(preset_number).isdigit()
        )
        return status

    def _snapshot_summary(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        content_item = snapshot.get("content_item") if isinstance(snapshot.get("content_item"), dict) else {}
        return {
            "observed_at": self._timestamp(),
            "preset_id": snapshot.get("preset_id"),
            "source": str((content_item or {}).get("source") or snapshot.get("source") or "").strip(),
            "item_name": str(snapshot.get("item_name") or snapshot.get("station_name") or "").strip(),
            "location": str((content_item or {}).get("location") or "").strip(),
        }

    def _record_event(
        self,
        ip_address: str,
        *,
        preset_number: int,
        trigger_mode: str,
        station_name: str,
        attempted: bool,
        result: str,
        error: str = "",
    ) -> None:
        status = self._ensure_device_status(ip_address)
        self._recent_events.append(
            {
                "timestamp_utc": self._timestamp(),
                "ip_address": ip_address,
                "preset_number": preset_number,
                "trigger_mode": trigger_mode,
                "station_name": station_name,
                "attempted": attempted,
                "result": result,
                "mapping_count": status["mapping_count"],
                "error": error,
            }
        )

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()
