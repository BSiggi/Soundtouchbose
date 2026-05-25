"""Best-effort preset bridge inference and playback control."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Callable

from soundtouchbose.api.client import SoundTouchClient, SoundTouchRequestError
from soundtouchbose.core.config import ConfigStore
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
        self._device_start_logged: set[str] = set()
        self._diagnostics: dict[str, dict[str, int | bool]] = {}

    def is_enabled(self) -> bool:
        return bool(self.config_store.load_settings().get("preset_bridge_enabled", False))

    def diagnostics(self) -> dict[str, dict[str, int | bool]]:
        return {ip: dict(values) for ip, values in self._diagnostics.items()}

    def handle_snapshot(self, ip_address: str, snapshot: dict[str, Any]) -> None:
        if not self.is_enabled():
            return
        stats = self._diagnostics.setdefault(
            ip_address,
            {
                "snapshots_seen": 0,
                "mapping_count": 0,
                "trigger_detected": 0,
                "trigger_missing": 0,
                "launch_attempted": 0,
                "launch_succeeded": 0,
                "launch_failed": 0,
                "detection_possible": False,
            },
        )
        stats["snapshots_seen"] = int(stats["snapshots_seen"]) + 1
        mapping_count = len(self.preset_manager.get_bridge_mappings(ip_address))
        stats["mapping_count"] = mapping_count
        if ip_address not in self._device_start_logged:
            self._device_start_logged.add(ip_address)
            LOGGER.info(
                "Preset bridge active device=%s mappings=%s detection=preset_id_or_now_playing_signature",
                ip_address,
                mapping_count,
            )
        preset_number = self._infer_preset_number(ip_address, snapshot)
        if preset_number is None:
            stats["trigger_missing"] = int(stats["trigger_missing"]) + 1
            misses = int(stats["trigger_missing"])
            if mapping_count and misses in {1, 10}:
                LOGGER.warning(
                    "Preset bridge enabled but no trigger detected for device=%s yet "
                    "(mappings=%s snapshots=%s). Some SoundTouch models do not expose preset button events.",
                    ip_address,
                    mapping_count,
                    stats["snapshots_seen"],
                )
            self._last_inferred_preset[ip_address] = None
            return
        if self._last_inferred_preset.get(ip_address) == preset_number:
            return
        self._last_inferred_preset[ip_address] = preset_number
        stats["trigger_detected"] = int(stats["trigger_detected"]) + 1
        stats["detection_possible"] = True
        station = self.preset_manager.get_bridge_station(ip_address, preset_number)
        if not station:
            LOGGER.info(
                "Preset bridge enabled but no local mapping for device=%s preset=%s",
                ip_address,
                preset_number,
            )
            return
        stats["launch_attempted"] = int(stats["launch_attempted"]) + 1
        LOGGER.info(
            "Preset bridge launch attempt device=%s preset=%s station=%s source=%s",
            ip_address,
            preset_number,
            station.name,
            station.source,
        )
        try:
            self.client_factory(ip_address).select(station)
        except SoundTouchRequestError as exc:
            stats["launch_failed"] = int(stats["launch_failed"]) + 1
            LOGGER.warning(
                "Preset bridge launch failed device=%s preset=%s station=%s endpoint=%s status=%s",
                ip_address,
                preset_number,
                station.name,
                exc.endpoint,
                exc.status_code,
            )
            return
        stats["launch_succeeded"] = int(stats["launch_succeeded"]) + 1
        LOGGER.info(
            "Preset bridge launch succeeded device=%s preset=%s station=%s source=%s endpoint=/select status=200",
            ip_address,
            preset_number,
            station.name,
            station.source,
        )

    def _infer_preset_number(self, ip_address: str, snapshot: dict[str, Any]) -> int | None:
        preset_id = snapshot.get("preset_id")
        if isinstance(preset_id, int) and 1 <= preset_id <= 6:
            LOGGER.info(
                "Preset bridge trigger detected device=%s preset=%s mode=direct",
                ip_address,
                preset_id,
            )
            return preset_id
        match = self._match_from_hardware_cache(ip_address, snapshot)
        if match is not None:
            LOGGER.info(
                "Preset bridge trigger inferred device=%s preset=%s mode=now_playing_signature",
                ip_address,
                match,
            )
        return match

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
