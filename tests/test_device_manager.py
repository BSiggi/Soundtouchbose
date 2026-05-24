from pathlib import Path

from soundtouchbose.core.config import ConfigStore
from soundtouchbose.core.device_manager import DeviceManager


class FakeClient:
    def get_info(self):
        return {"name": "BÃRO", "mac_address": "AA:BB", "type": "SoundTouch", "software_version": "1.0"}

    def get_now_playing(self):
        raise RuntimeError("SoundTouch HTTP 500 for http://192.168.1.2:8090/now_playing")


def test_add_manual_device_handles_now_playing_failure_without_firewall_text(tmp_path: Path) -> None:
    store = ConfigStore(tmp_path)
    manager = DeviceManager(store, client_factory=lambda _ip: FakeClient())

    device = manager.add_manual_device("192.168.1.2")

    assert device.name == "BÜRO"
    assert device.reachable is True
    assert device.service_available is True
    assert device.source == "Quelle derzeit nicht lesbar"
    assert "Firewall" not in device.error_text
    assert device.last_error_details
    assert device.last_error_details["operation"] == "now_playing"
