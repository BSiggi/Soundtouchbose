from pathlib import Path

from soundtouchbose.core.config import ConfigStore
from soundtouchbose.core.device_manager import Device
from soundtouchbose.core.preset_bridge import PresetBridgeService
from soundtouchbose.core.preset_manager import PresetManager
from soundtouchbose.core.station_library import Station, StationLibrary


class FakeDeviceManager:
    def __init__(self, ip_address: str) -> None:
        self._devices = [Device(name="BÜRO", ip_address=ip_address)]

    def all_devices(self):
        return self._devices


class FakeClient:
    def __init__(self, presets, now_playing):
        self._presets = presets
        self._now_playing = now_playing
        self.selected = []

    def get_presets(self):
        return self._presets

    def get_now_playing(self):
        return self._now_playing

    def select(self, station):
        self.selected.append(station.identifier)


def test_preset_bridge_detects_trigger_and_starts_mapped_station(tmp_path: Path) -> None:
    ip_address = "192.168.100.148"
    config_store = ConfigStore(tmp_path / "config")
    config_store.save_settings({"preset_bridge_enabled": True})
    station_library = StationLibrary(config_store)
    preset_manager = PresetManager(config_store, client_factory=lambda _ip: None)
    mapped_station = Station(
        identifier="bridge-station",
        name="Bridge Station",
        category="Custom",
        source="INTERNET_RADIO",
        location="https://example.test/live.mp3",
    )
    preset_manager.assign_bridge_rule(ip_address, 1, mapped_station)
    fake_client = FakeClient(
        presets=[{"id": 1, "source": "TUNEIN", "location": "/v1/playback/station/s24875"}],
        now_playing={
            "source": "TUNEIN",
            "content_item": {"source": "TUNEIN", "location": "/v1/playback/station/s24875"},
        },
    )
    service = PresetBridgeService(
        config_store=config_store,
        device_manager=FakeDeviceManager(ip_address),
        preset_manager=preset_manager,
        station_library=station_library,
        client_factory=lambda _ip: fake_client,
    )

    service._poll_device(ip_address)
    assert fake_client.selected == ["bridge-station"]
    service._poll_device(ip_address)

    assert fake_client.selected == ["bridge-station"]
    assert service.snapshot()["events"][-1]["success"] is True


def test_preset_bridge_records_trigger_without_rule(tmp_path: Path) -> None:
    ip_address = "192.168.100.149"
    config_store = ConfigStore(tmp_path / "config")
    station_library = StationLibrary(config_store)
    preset_manager = PresetManager(config_store, client_factory=lambda _ip: None)
    fake_client = FakeClient(
        presets=[{"id": 2, "source": "TUNEIN", "location": "/v1/playback/station/s777"}],
        now_playing={
            "source": "TUNEIN",
            "content_item": {"source": "TUNEIN", "location": "/v1/playback/station/s777"},
        },
    )
    service = PresetBridgeService(
        config_store=config_store,
        device_manager=FakeDeviceManager(ip_address),
        preset_manager=preset_manager,
        station_library=station_library,
        client_factory=lambda _ip: fake_client,
    )

    service._poll_device(ip_address)

    assert fake_client.selected == []
    assert service.snapshot()["events"][-1]["detail"] == "no_rule"


def test_preset_bridge_snapshot_uses_configured_poll_interval(tmp_path: Path) -> None:
    config_store = ConfigStore(tmp_path / "config")
    config_store.save_settings({"preset_bridge_poll_interval_seconds": 1.5})
    station_library = StationLibrary(config_store)
    preset_manager = PresetManager(config_store, client_factory=lambda _ip: None)
    service = PresetBridgeService(
        config_store=config_store,
        device_manager=FakeDeviceManager("192.168.100.150"),
        preset_manager=preset_manager,
        station_library=station_library,
        client_factory=lambda _ip: FakeClient([], {"content_item": {}}),
    )

    assert service.snapshot()["poll_interval_seconds"] == 1.5


def test_match_preset_number_requires_source_and_location() -> None:
    assert PresetBridgeService._match_preset_number([], {"content_item": {}}) is None
