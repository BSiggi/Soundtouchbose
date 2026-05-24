"""Optional bridge that treats hardware preset keys as app-defined triggers."""

from __future__ import annotations

import logging
import threading
import time
from collections import deque
from collections.abc import Callable
from typing import Any

from soundtouchbose.api.client import SoundTouchClient
from soundtouchbose.core.config import ConfigStore
from soundtouchbose.core.device_manager import DeviceManager
from soundtouchbose.core.preset_manager import PresetManager
from soundtouchbose.core.station_library import Station, StationLibrary

LOGGER = logging.getLogger(__name__)


class PresetBridgeService:
    """Poll now_playing and infer preset-trigger events when bridge mode is enabled."""

    def __init__(
        self,
        config_store: ConfigStore,
        device_manager: DeviceManager,
        preset_manager: PresetManager,
        station_library: StationLibrary,
        client_factory: Callable[[str], SoundTouchClient] = SoundTouchClient,
        *,
        poll_interval_seconds: float = 3.0,
    ) -> None:
        self.config_store = config_store
        self.device_manager = device_manager
        self.preset_manager = preset_manager
        self.station_library = station_library
        self.client_factory = client_factory
        self.poll_interval_seconds = poll_interval_seconds
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._last_signature: dict[str, tuple[int, str, str] | None] = {}
        self._events: deque[dict[str, Any]] = deque(maxlen=100)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="preset-bridge")
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def snapshot(self) -> dict[str, Any]:
        settings = self.config_store.load_settings()
        poll_interval = self._poll_interval_from_settings(settings)
        return {
            "enabled": bool(settings.get("preset_bridge_enabled", False)),
            "poll_interval_seconds": poll_interval,
            "events": list(self._events),
        }

    def _record_event(
        self,
        ip_address: str,
        preset_number: int,
        *,
        action: str,
        success: bool,
        detail: str = "",
    ) -> None:
        self._events.append(
            {
                "ip_address": ip_address,
                "preset_number": preset_number,
                "action": action,
                "success": success,
                "detail": detail,
                "timestamp_unix": time.time(),
            }
        )

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            settings = self.config_store.load_settings()
            enabled = bool(settings.get("preset_bridge_enabled", False))
            poll_interval = self._poll_interval_from_settings(settings)
            if not enabled:
                self._last_signature.clear()
                self._stop_event.wait(min(1.0, poll_interval))
                continue
            for device in self.device_manager.all_devices():
                if not device.ip_address:
                    continue
                try:
                    self._poll_device(device.ip_address)
                except Exception as exc:
                    LOGGER.warning("Preset bridge polling failed for %s: %s", device.ip_address, exc)
            self._stop_event.wait(poll_interval)

    def _poll_device(self, ip_address: str) -> None:
        client = self.client_factory(ip_address)
        now_playing = client.get_now_playing()
        matched_preset = self._match_preset_number(client.get_presets(), now_playing)
        if matched_preset is None:
            self._last_signature[ip_address] = None
            return
        content_item = now_playing.get("content_item") or {}
        signature = (
            matched_preset,
            str(content_item.get("source", now_playing.get("source", ""))),
            str(content_item.get("location", "")),
        )
        if self._last_signature.get(ip_address) == signature:
            return
        self._last_signature[ip_address] = signature
        station_payload = self.preset_manager.get_cached_presets(ip_address).get(str(matched_preset))
        if not station_payload:
            LOGGER.info(
                "Preset bridge trigger erkannt: %s Preset %s ohne App-Regel",
                ip_address,
                matched_preset,
            )
            self._record_event(ip_address, matched_preset, action="trigger_detected", success=False, detail="no_rule")
            return
        station = Station.from_dict(station_payload)
        LOGGER.info(
            "Preset bridge trigger erkannt: %s Preset %s -> %s",
            ip_address,
            matched_preset,
            station.name,
        )
        try:
            client.select(station)
        except Exception as exc:
            LOGGER.warning(
                "Preset bridge Ausführung fehlgeschlagen für %s Preset %s: %s",
                ip_address,
                matched_preset,
                exc,
            )
            self._record_event(
                ip_address,
                matched_preset,
                action="bridge_select",
                success=False,
                detail=str(exc),
            )
            return
        self._record_event(
            ip_address,
            matched_preset,
            action="bridge_select",
            success=True,
            detail=station.name,
        )
        LOGGER.info(
            "Preset bridge erfolgreich: %s Preset %s startet %s",
            ip_address,
            matched_preset,
            station.name,
        )

    @staticmethod
    def _match_preset_number(presets: list[dict[str, Any]], now_playing: dict[str, Any]) -> int | None:
        content_item = now_playing.get("content_item") or {}
        current_location = str(content_item.get("location", "")).strip()
        current_source = str(content_item.get("source", now_playing.get("source", ""))).strip().upper()
        if not current_location or not current_source:
            return None
        for preset in presets:
            location = str(preset.get("location", "")).strip()
            source = str(preset.get("source", "")).strip().upper()
            if location == current_location and source == current_source:
                try:
                    return int(preset.get("id", 0))
                except (TypeError, ValueError):
                    return None
        return None

    def _poll_interval_from_settings(self, settings: dict[str, Any]) -> float:
        raw_value = settings.get("preset_bridge_poll_interval_seconds", self.poll_interval_seconds)
        try:
            parsed = float(raw_value)
        except (TypeError, ValueError):
            return self.poll_interval_seconds
        return max(0.5, min(30.0, parsed))
