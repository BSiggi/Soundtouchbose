from pathlib import Path

from soundtouchbose.core.config import ConfigStore
from soundtouchbose.core.preset_bridge import PresetBridgeController
from soundtouchbose.core.preset_manager import PresetManager
from soundtouchbose.core.station_library import Station


class FakeClient:
    def __init__(self) -> None:
        self.selected = []
        self.presets = []

    def select(self, station) -> None:
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


def test_bridge_status_reports_missing_trigger_when_snapshots_have_no_detected_preset(tmp_path: Path) -> None:
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

    bridge.handle_snapshot("192.168.1.4", {"source": "AUX"})

    assert "kein Preset-Trigger erkannt" in bridge.status_message("192.168.1.4")


def test_bridge_diagnostics_snapshot_contains_recent_events(tmp_path: Path) -> None:
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
    snapshot = bridge.diagnostics_snapshot()

    assert snapshot["devices"]["192.168.1.4"]["last_launch_status"] == "success"
    assert any(event["event"] == "launch_succeeded" for event in snapshot["recent_events"])
