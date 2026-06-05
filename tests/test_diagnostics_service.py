from pathlib import Path
from types import SimpleNamespace
from zipfile import ZipFile

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
        return {"127.0.0.1": {"1": {"name": "Bridge Test"}}}


class FakePresetBridge:
    def diagnostics_snapshot(self):
        return {
            "enabled": True,
            "devices": {
                "127.0.0.1": {
                    "bridge_enabled": True,
                    "mappings_loaded": True,
                    "mapping_count": 1,
                    "mapped_presets": [1],
                    "last_trigger": {"detected": True, "preset_number": 1, "mode": "direct"},
                    "last_launch": {"attempted": True, "result": "succeeded", "station_name": "Bridge Test"},
                }
            },
            "recent_events": [{"result": "succeeded", "ip_address": "127.0.0.1", "preset_number": 1}],
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
    assert report["preset_bridge"]["enabled"] is True
    assert report["preset_bridge"]["mapped_slots"] == 1
    assert report["preset_bridge"]["devices"]["127.0.0.1"]["last_launch"]["result"] == "succeeded"
    assert created.exists()
    assert created == destination
    with ZipFile(created) as archive:
        names = set(archive.namelist())
    assert "diagnostics/preset_bridge_mappings.json" in names
    assert "diagnostics/preset_bridge_status.json" in names
