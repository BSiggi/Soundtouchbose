"""Shared service container types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from soundtouchbose.api.client import SoundTouchClient
from soundtouchbose.core.cleanup_service import CleanupService
from soundtouchbose.core.config import ConfigStore
from soundtouchbose.core.diagnostics_service import DiagnosticsService
from soundtouchbose.core.device_manager import DeviceManager
from soundtouchbose.core.preset_manager import PresetManager
from soundtouchbose.core.scheduler import SchedulerService
from soundtouchbose.core.station_library import StationLibrary
from soundtouchbose.core.update_manager import UpdateManager
from soundtouchbose.core.zone_manager import ZoneManager


@dataclass(slots=True)
class Services:
    config_store: ConfigStore
    device_manager: DeviceManager
    station_library: StationLibrary
    preset_manager: PresetManager
    zone_manager: ZoneManager
    scheduler: SchedulerService
    update_manager: UpdateManager
    diagnostics_service: DiagnosticsService
    cleanup_service: CleanupService
    client_factory: Callable[[str], SoundTouchClient]
