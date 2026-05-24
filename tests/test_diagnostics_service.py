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


def test_diagnostics_export_masks_sensitive_settings(tmp_path: Path) -> None:
    config_store = ConfigStore(tmp_path / "config")
    config_store.save_settings({"home_assistant_token": "secret-token"})
    context = SimpleNamespace(config_store=config_store, device_manager=FakeDeviceManager())
    service = DiagnosticsService(context)
    destination = tmp_path / "diagnostics.zip"

    report = service.collect_report()
    service.record_device_error("127.0.0.1", "now_playing", RuntimeError("SoundTouch request failed for http://127.0.0.1:8090/now_playing"))
    report_with_error = service.collect_report()
    created = service.export(destination)

    assert report["settings"]["home_assistant_token"] == "***masked***"
    assert report_with_error["device_last_errors"]["127.0.0.1"]["operation"] == "now_playing"
    assert created.exists()
    assert created == destination
