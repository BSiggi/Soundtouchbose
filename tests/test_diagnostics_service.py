from pathlib import Path
from types import SimpleNamespace

from soundtouchbose.core.config import ConfigStore
from soundtouchbose.core.device_manager import Device
from soundtouchbose.core.diagnostics_service import DiagnosticsService


class FakeDeviceManager:
    def all_devices(self):
        return [
            Device(
                name="Wohnzimmer",
                ip_address="127.0.0.1",
                source="Internetradio",
                source_raw="TUNEIN",
                online=True,
                reachable=True,
                service_available=True,
                source_valid=True,
            )
        ]


class FakePresetManager:
    def load_bridge_mappings(self):
        return {"127.0.0.1": {"1": {"identifier": "bridge-1", "name": "Bridge Test", "source": "TUNEIN", "location": "/v1/playback/station/s1"}}}


class FakePresetBridge:
    def diagnostics_snapshot(self):
        return {
            "devices": {"127.0.0.1": {"snapshots_seen": 3, "last_launch_status": "failed"}},
            "recent_events": [{"event": "launch_failed", "device_ip": "127.0.0.1"}],
        }


def test_diagnostics_export_masks_sensitive_settings(tmp_path: Path) -> None:
    config_store = ConfigStore(tmp_path / "config")
    config_store.save_settings({"home_assistant_token": "secret-token"})
    context = SimpleNamespace(
        config_store=config_store,
        device_manager=FakeDeviceManager(),
        preset_manager=FakePresetManager(),
        preset_bridge=FakePresetBridge(),
    )
    service = DiagnosticsService(context)
    destination = tmp_path / "diagnostics.zip"

    report = service.collect_report()
    created = service.export(destination)

    assert report["settings"]["home_assistant_token"] == "***masked***"
    assert report["preset_bridge"]["enabled"] is False
    assert report["preset_bridge"]["mapped_slots"] == 1
    assert report["preset_bridge"]["configured_mappings"]["127.0.0.1"]["1"]["name"] == "Bridge Test"
    assert report["preset_bridge"]["runtime"]["devices"]["127.0.0.1"]["last_launch_status"] == "failed"
    assert created.exists()
    assert created == destination
