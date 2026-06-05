from soundtouchbose.api.client import SoundTouchRequestError
from pathlib import Path

from soundtouchbose.core.config import ConfigStore
from soundtouchbose.core.preset_bridge import PresetBridgeController
from soundtouchbose.core.preset_manager import PresetManager
from soundtouchbose.core.station_library import Station


class FakeClient:
    def __init__(self) -> None:
        self.selected = []
        self.presets = []
        self.select_error: SoundTouchRequestError | None = None

    def select(self, station) -> None:
        if self.select_error is not None:
            raise self.select_error
        self.selected.append(station.identifier)

    def get_presets(self):
        return list(self.presets)


def test_bridge_does_not_trigger_when_disabled(tmp_path: Path) -> None:
    config_store = ConfigStore(tmp_path)
    client = FakeClient()
    preset_manager = PresetManager(config_store, client_factory=lambda _ip: client)
    bridge = PresetBridgeController(config_store, preset_manager, lambda _ip: client)

    bridge.handle_snapshot("192.168.1.4", {"preset_id": 1})

    assert client.selected == []


def test_bridge_uses_local_mapping_for_direct_preset_id(tmp_path: Path) -> None:
    config_store = ConfigStore(tmp_path)
    config_store.save_settings({"preset_bridge_enabled": True})
    client = FakeClient()
    preset_manager = PresetManager(config_store, client_factory=lambda _ip: client)
    station = Station(
        identifier="s100",
        name="Bridge Station",
        category="News",
        source="INTERNET_RADIO",
        location="http://example.test/news",
    )
    preset_manager.assign_bridge_mapping("192.168.1.4", 1, station)
    bridge = PresetBridgeController(config_store, preset_manager, lambda _ip: client)

    bridge.handle_snapshot("192.168.1.4", {"preset_id": 1})

    assert client.selected == ["s100"]
    status = bridge.get_device_status("192.168.1.4")
    assert status["mappings_loaded"] is True
    assert status["last_trigger"]["preset_number"] == 1
    assert status["last_launch"]["result"] == "succeeded"


def test_bridge_infers_preset_from_now_playing_signature(tmp_path: Path) -> None:
    config_store = ConfigStore(tmp_path)
    config_store.save_settings({"preset_bridge_enabled": True})
    client = FakeClient()
    client.presets = [
        {"id": 2, "source": "TUNEIN", "location": "/v1/playback/station/s24875", "name": "Deutschlandfunk"}
    ]
    preset_manager = PresetManager(config_store, client_factory=lambda _ip: client)
    station = Station(
        identifier="local-2",
        name="Lokaler Stream 2",
        category="Custom",
        source="INTERNET_RADIO",
        location="http://example.test/local2",
    )
    preset_manager.assign_bridge_mapping("192.168.1.8", 2, station)
    bridge = PresetBridgeController(config_store, preset_manager, lambda _ip: client)

    bridge.handle_snapshot(
        "192.168.1.8",
        {
            "source": "TUNEIN",
            "item_name": "Deutschlandfunk",
            "content_item": {"source": "TUNEIN", "location": "/v1/playback/station/s24875"},
        },
    )

    assert client.selected == ["local-2"]


def test_bridge_status_reports_missing_mapping(tmp_path: Path) -> None:
    config_store = ConfigStore(tmp_path)
    config_store.save_settings({"preset_bridge_enabled": True})
    client = FakeClient()
    preset_manager = PresetManager(config_store, client_factory=lambda _ip: client)
    bridge = PresetBridgeController(config_store, preset_manager, lambda _ip: client)

    bridge.handle_snapshot("192.168.1.5", {"preset_id": 3})

    status = bridge.get_device_status("192.168.1.5")
    assert status["mappings_loaded"] is False
    assert status["last_launch"]["result"] == "no_mapping"
    assert bridge.diagnostics_snapshot()["recent_events"][-1]["result"] == "no_mapping"


def test_bridge_status_reports_failed_launch(tmp_path: Path) -> None:
    config_store = ConfigStore(tmp_path)
    config_store.save_settings({"preset_bridge_enabled": True})
    client = FakeClient()
    client.select_error = SoundTouchRequestError("http://192.168.1.9:8090/select", status_code=500, details="boom")
    preset_manager = PresetManager(config_store, client_factory=lambda _ip: client)
    station = Station(
        identifier="s500",
        name="Fehler Stream",
        category="Custom",
        source="INTERNET_RADIO",
        location="http://example.test/fail",
    )
    preset_manager.assign_bridge_mapping("192.168.1.9", 4, station)
    bridge = PresetBridgeController(config_store, preset_manager, lambda _ip: client)

    bridge.handle_snapshot("192.168.1.9", {"preset_id": 4})

    status = bridge.get_device_status("192.168.1.9")
    assert status["last_launch"]["result"] == "failed"
    assert status["last_launch"]["status_code"] == 500
    assert bridge.diagnostics_snapshot()["recent_events"][-1]["result"] == "failed"
