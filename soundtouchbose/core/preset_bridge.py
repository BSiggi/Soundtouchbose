"""Best-effort preset bridge inference and playback control."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Any, Callable

from soundtouchbose.api.client import SoundTouchClient, SoundTouchRequestError
from soundtouchbose.core.config import ConfigStore
from soundtouchbose.core.preset_manager import PresetManager

LOGGER = logging.getLogger(__name__)
HARDWARE_PRESET_CACHE_TTL_SECONDS = 300
NO_TRIGGER_WARNING_INTERVAL_SECONDS = 30
MAX_RECENT_EVENTS = 100


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
        self._snapshot_count: dict[str, int] = {}
        self._no_trigger_count: dict[str, int] = {}
        self._last_trigger_at: dict[str, str] = {}
        self._last_trigger_mode: dict[str, str] = {}
        self._last_trigger_preset: dict[str, int] = {}
        self._last_launch_status: dict[str, str] = {}
        self._last_launch_error: dict[str, str] = {}
        self._last_launch_at: dict[str, str] = {}
        self._last_snapshot_at: dict[str, str] = {}
        self._last_no_trigger_warning_at: dict[str, float] = {}
        self._recent_events: list[dict[str, object]] = []

    @staticmethod
    def _utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _record_event(self, event: str, ip_address: str, **details: object) -> None:
        payload = {"timestamp_utc": self._utc_now_iso(), "event": event, "device_ip": ip_address, **details}
        self._recent_events.append(payload)
        if len(self._recent_events) > MAX_RECENT_EVENTS:
            self._recent_events = self._recent_events[-MAX_RECENT_EVENTS:]

    def is_enabled(self) -> bool:
        return bool(self.config_store.load_settings().get("preset_bridge_enabled", False))

    def handle_snapshot(self, ip_address: str, snapshot: dict[str, Any]) -> None:
        if not self.is_enabled():
            return
        self._snapshot_count[ip_address] = self._snapshot_count.get(ip_address, 0) + 1
        self._last_snapshot_at[ip_address] = self._utc_now_iso()
        preset_number = self._infer_preset_number(ip_address, snapshot)
        if preset_number is None:
            self._no_trigger_count[ip_address] = self._no_trigger_count.get(ip_address, 0) + 1
            mappings = self.preset_manager.get_bridge_mappings(ip_address)
            if mappings:
                last_warning = self._last_no_trigger_warning_at.get(ip_address, 0.0)
                now = time.time()
                if now - last_warning >= NO_TRIGGER_WARNING_INTERVAL_SECONDS:
                    LOGGER.warning(
                        "Preset bridge active but no hardware trigger detected device=%s snapshots=%s configured_slots=%s",
                        ip_address,
                        self._snapshot_count[ip_address],
                        len(mappings),
                    )
                    self._last_no_trigger_warning_at[ip_address] = now
                    self._record_event(
                        "no_trigger_detected",
                        ip_address,
                        snapshots=self._snapshot_count[ip_address],
                        configured_slots=len(mappings),
                    )
            self._last_inferred_preset[ip_address] = None
            return
        if self._last_inferred_preset.get(ip_address) == preset_number:
            return
        self._last_inferred_preset[ip_address] = preset_number
        station = self.preset_manager.get_bridge_station(ip_address, preset_number)
        self._last_trigger_at[ip_address] = self._utc_now_iso()
        self._last_trigger_preset[ip_address] = preset_number
        if not station:
            self._last_launch_status[ip_address] = "missing_mapping"
            self._last_launch_error[ip_address] = ""
            LOGGER.info(
                "Preset bridge enabled but no local mapping for device=%s preset=%s",
                ip_address,
                preset_number,
            )
            self._record_event("missing_mapping", ip_address, preset=preset_number)
            return
        self._last_launch_at[ip_address] = self._utc_now_iso()
        self._record_event("launch_attempt", ip_address, preset=preset_number, station=station.name, source=station.source)
        try:
            self.client_factory(ip_address).select(station)
        except SoundTouchRequestError as exc:
            self._last_launch_status[ip_address] = "failed"
            self._last_launch_error[ip_address] = f"{exc.endpoint} status={exc.status_code}"
            LOGGER.warning(
                "Preset bridge launch failed device=%s preset=%s station=%s endpoint=%s status=%s",
                ip_address,
                preset_number,
                station.name,
                exc.endpoint,
                exc.status_code,
            )
            self._record_event(
                "launch_failed",
                ip_address,
                preset=preset_number,
                station=station.name,
                endpoint=exc.endpoint,
                status=exc.status_code,
            )
            return
        self._last_launch_status[ip_address] = "success"
        self._last_launch_error[ip_address] = ""
        LOGGER.info(
            "Preset bridge launch succeeded device=%s preset=%s station=%s source=%s endpoint=/select status=200",
            ip_address,
            preset_number,
            station.name,
            station.source,
        )
        self._record_event("launch_succeeded", ip_address, preset=preset_number, station=station.name, source=station.source)

    def _infer_preset_number(self, ip_address: str, snapshot: dict[str, Any]) -> int | None:
        preset_id = snapshot.get("preset_id")
        if isinstance(preset_id, int) and 1 <= preset_id <= 6:
            self._last_trigger_mode[ip_address] = "direct"
            LOGGER.info(
                "Preset bridge trigger detected device=%s preset=%s mode=direct",
                ip_address,
                preset_id,
            )
            return preset_id
        match = self._match_from_hardware_cache(ip_address, snapshot)
        if match is not None:
            self._last_trigger_mode[ip_address] = "now_playing_signature"
            LOGGER.info(
                "Preset bridge trigger inferred device=%s preset=%s mode=now_playing_signature",
                ip_address,
                match,
            )
        return match

    def status_for_device(self, ip_address: str) -> dict[str, object]:
        return {
            "snapshots_seen": self._snapshot_count.get(ip_address, 0),
            "no_trigger_snapshots": self._no_trigger_count.get(ip_address, 0),
            "last_snapshot_at_utc": self._last_snapshot_at.get(ip_address, ""),
            "last_trigger_at_utc": self._last_trigger_at.get(ip_address, ""),
            "last_trigger_mode": self._last_trigger_mode.get(ip_address, ""),
            "last_trigger_preset": self._last_trigger_preset.get(ip_address),
            "last_launch_status": self._last_launch_status.get(ip_address, ""),
            "last_launch_error": self._last_launch_error.get(ip_address, ""),
            "last_launch_at_utc": self._last_launch_at.get(ip_address, ""),
            "configured_slots": len(self.preset_manager.get_bridge_mappings(ip_address)),
        }

    def status_message(self, ip_address: str) -> str:
        status = self.status_for_device(ip_address)
        configured_slots = int(status["configured_slots"])
        snapshots_seen = int(status["snapshots_seen"])
        no_trigger_snapshots = int(status["no_trigger_snapshots"])
        last_launch_status = str(status["last_launch_status"])
        if configured_slots == 0:
            return "Preset-Bridge aktiv, aber für dieses Gerät sind noch keine lokalen Tasten-Zuordnungen gespeichert."
        if snapshots_seen == 0:
            return "Preset-Bridge aktiv. Warte auf erste Statusdaten vom Gerät (Dashboard/Live-Status)."
        if not status["last_trigger_at_utc"]:
            return (
                f"Preset-Bridge aktiv, aber noch kein Preset-Trigger erkannt "
                f"({no_trigger_snapshots} Status-Updates ohne Tastenevent). "
                "Einige SoundTouch-Geräte liefern nach EOL keine zuverlässigen Preset-Events."
            )
        if last_launch_status == "failed":
            return f"Letzter Stream-Start fehlgeschlagen: {status['last_launch_error']}"
        if last_launch_status == "missing_mapping":
            return "Preset erkannt, aber keine lokale Zuordnung für diese Taste gefunden."
        if last_launch_status == "success":
            return "Preset erkannt und lokaler Stream-Start wurde ausgelöst."
        return "Preset erkannt. Weitere Details im Diagnose-Export (Preset-Bridge-Runtime)."

    def diagnostics_snapshot(self) -> dict[str, object]:
        return {
            "devices": {
                ip: self.status_for_device(ip)
                for ip in sorted(
                    set(self._snapshot_count)
                    | set(self._last_launch_status)
                    | set(self._last_trigger_at)
                    | set(self._no_trigger_count)
                )
            },
            "recent_events": list(self._recent_events[-50:]),
        }

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
