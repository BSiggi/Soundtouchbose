"""Shared service container types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from soundtouchbose.api.client import SoundTouchClient
from soundtouchbose.core.config import ConfigStore
from soundtouchbose.core.device_manager import DeviceManager
from soundtouchbose.core.preset_manager import PresetManager
from soundtouchbose.core.scheduler import SchedulerService
from soundtouchbose.core.station_library import StationLibrary
from soundtouchbose.core.zone_manager import ZoneManager


@dataclass(slots=True)
class Services:
    config_store: ConfigStore
    device_manager: DeviceManager
    station_library: StationLibrary
    preset_manager: PresetManager
    zone_manager: ZoneManager
    scheduler: SchedulerService
    client_factory: Callable[[str], SoundTouchClient]
