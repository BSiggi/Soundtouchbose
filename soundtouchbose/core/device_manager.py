"""Known device persistence and refresh helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Callable

from soundtouchbose.api.client import SoundTouchClient
from soundtouchbose.api.discovery import discover_once
from soundtouchbose.core.config import ConfigStore


@dataclass(slots=True)
class Device:
    name: str
    ip_address: str
    mac_address: str = ""
    model: str = ""
    firmware: str = ""
    online: bool = False
    source: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "Device":
        return cls(
            name=str(payload.get("name", "Unknown")),
            ip_address=str(payload.get("ip_address") or payload.get("ip") or ""),
            mac_address=str(payload.get("mac_address", "")),
            model=str(payload.get("model", "")),
            firmware=str(payload.get("firmware", "")),
            online=bool(payload.get("online", False)),
            source=str(payload.get("source", "")),
        )


class DeviceManager:
    """Manage known SoundTouch devices."""

    def __init__(self, config_store: ConfigStore, client_factory: Callable[[str], SoundTouchClient] = SoundTouchClient) -> None:
        self.config_store = config_store
        self.client_factory = client_factory
        self.devices: dict[str, Device] = {}
        self.load()

    def load(self) -> None:
        payload = self.config_store.load_json("devices.json", [])
        self.devices = {entry["ip_address"]: Device.from_dict(entry) for entry in payload if entry.get("ip_address")}

    def save(self) -> None:
        self.config_store.save_json("devices.json", [device.to_dict() for device in self.devices.values()])

    def all_devices(self) -> list[Device]:
        return sorted(self.devices.values(), key=lambda device: device.name.lower())

    def add_manual_device(self, ip_address: str) -> Device:
        client = self.client_factory(ip_address)
        info = client.get_info()
        now_playing = client.get_now_playing()
        device = Device(
            name=info.get("name") or ip_address,
            ip_address=ip_address,
            mac_address=info.get("mac_address", ""),
            model=info.get("type", ""),
            firmware=info.get("software_version", ""),
            online=True,
            source=now_playing.get("item_name") or now_playing.get("station_name") or now_playing.get("source", ""),
        )
        self.devices[ip_address] = device
        self.save()
        return device

    def remove_device(self, ip_address: str) -> None:
        self.devices.pop(ip_address, None)
        self.save()

    def refresh_device(self, ip_address: str) -> Device | None:
        if ip_address not in self.devices:
            return None
        try:
            device = self.add_manual_device(ip_address)
            device.online = True
        except Exception:
            device = self.devices[ip_address]
            device.online = False
            self.save()
        return device

    def rescan(self) -> list[Device]:
        for discovered in discover_once():
            try:
                self.add_manual_device(discovered.ip_address)
            except Exception:
                self.devices.setdefault(
                    discovered.ip_address,
                    Device(name=discovered.name, ip_address=discovered.ip_address, online=False),
                )
        self.save()
        return self.all_devices()
