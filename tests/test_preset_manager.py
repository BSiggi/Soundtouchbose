from pathlib import Path

from soundtouchbose.core.config import ConfigStore
from soundtouchbose.core.preset_manager import PresetManager
from soundtouchbose.core.station_library import Station


class FakeClient:
    def __init__(self, presets=None):
        self.assigned = []
        self._presets = presets or []

    def set_preset(self, preset_number, station):
        self.assigned.append((preset_number, station.identifier))
        return True

    def get_presets(self):
        return self._presets


def test_assign_preset_updates_cache(tmp_path: Path) -> None:
    fake_client = FakeClient()
    manager = PresetManager(ConfigStore(tmp_path), client_factory=lambda _ip: fake_client)
    station = Station(
        identifier="s24875",
        name="Deutschlandfunk",
        category="News",
        source="TUNEIN",
        location="/v1/playback/station/s24875",
    )

    result = manager.assign_preset("192.168.1.2", 1, station)

    assert result is True
    assert fake_client.assigned == [(1, "s24875")]
    assert manager.get_cached_presets("192.168.1.2")["1"]["name"] == "Deutschlandfunk"


def test_sync_presets_from_device_persists_snapshot(tmp_path: Path) -> None:
    fake_client = FakeClient(
        presets=[{"id": 1, "name": "SWR3", "source": "TUNEIN", "location": "/v1/playback/station/s24896"}]
    )
    manager = PresetManager(ConfigStore(tmp_path), client_factory=lambda _ip: fake_client)

    presets = manager.sync_presets_from_device("192.168.1.5")

    assert presets[0]["name"] == "SWR3"
    assert manager.get_cached_presets("192.168.1.5")["1"]["location"] == "/v1/playback/station/s24896"


def test_assign_bridge_mapping_persists_locally(tmp_path: Path) -> None:
    fake_client = FakeClient()
    manager = PresetManager(ConfigStore(tmp_path), client_factory=lambda _ip: fake_client)
    station = Station(
        identifier="s42",
        name="Teststream",
        category="Custom",
        source="INTERNET_RADIO",
        location="http://example.test/stream.mp3",
    )

    manager.assign_bridge_mapping("192.168.1.8", 2, station)

    bridge_station = manager.get_bridge_station("192.168.1.8", 2)
    assert bridge_station is not None
    assert bridge_station.name == "Teststream"
    assert fake_client.assigned == []
