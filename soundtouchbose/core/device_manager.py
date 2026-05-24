"""Known device persistence and refresh helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Callable

from soundtouchbose.api.client import SoundTouchClient
from soundtouchbose.api.discovery import discover_once
from soundtouchbose.core.config import ConfigStore
from soundtouchbose.core.error_texts import condition_error_details, error_details, is_valid_source, source_display_text, user_error_text
from soundtouchbose.core.text_utils import repair_mojibake


@dataclass(slots=True)
class Device:
    name: str
    ip_address: str
    mac_address: str = ""
    model: str = ""
    firmware: str = ""
    online: bool = False
    source: str = ""
    source_raw: str = ""
    reachable: bool = False
    service_available: bool = False
    source_valid: bool = False
    error_text: str = ""
    last_error_details: dict[str, object] | None = None

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
            source_raw=str(payload.get("source_raw", "")),
            reachable=bool(payload.get("reachable", payload.get("online", False))),
            service_available=bool(payload.get("service_available", payload.get("online", False))),
            source_valid=bool(payload.get("source_valid", True)),
            error_text=str(payload.get("error_text", "")),
            last_error_details=payload.get("last_error_details") if isinstance(payload.get("last_error_details"), dict) else None,
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
        name = repair_mojibake(str(info.get("name") or ip_address))
        source_raw = ""
        source_valid = False
        source = "Quelle derzeit nicht lesbar"
        error_text = ""
        last_error = None
        try:
            now_playing = client.get_now_playing()
            source_raw = str(now_playing.get("source", ""))
            source_valid = is_valid_source(source_raw)
            source = source_display_text(source_raw, now_playing)
            error_text = "" if source_valid else "Gerät ist erreichbar, aber die Quelle ist derzeit nicht lesbar (INVALID_SOURCE)."
            if not source_valid:
                last_error = condition_error_details(
                    operation="now_playing",
                    category="invalid_source",
                    message="Gerät meldet INVALID_SOURCE",
                    endpoint="/now_playing",
                )
        except Exception as exc:
            details = error_details(exc, operation="now_playing")
            details["endpoint"] = details.get("endpoint") or "/now_playing"
            last_error = details
            error_text = "Gerät ist erreichbar, aber die Quelle ist derzeit nicht lesbar."
            if details.get("category") in {"network", "timeout"}:
                error_text = user_error_text(exc)
        device = Device(
            name=name,
            ip_address=ip_address,
            mac_address=info.get("mac_address", ""),
            model=info.get("type", ""),
            firmware=info.get("software_version", ""),
            online=True,
            source=source,
            source_raw=source_raw,
            reachable=True,
            service_available=True,
            source_valid=source_valid,
            error_text=error_text,
            last_error_details=last_error,
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
        except Exception as exc:
            device = self.devices[ip_address]
            device.online = False
            device.reachable = False
            device.service_available = False
            device.source_valid = False
            device.error_text = user_error_text(exc)
            device.last_error_details = error_details(exc, operation="refresh_device")
            self.save()
        return device

    def rescan(self) -> list[Device]:
        known_ips = {device.ip_address for device in self.devices.values()}
        for discovered in discover_once():
            try:
                self.add_manual_device(discovered.ip_address)
            except Exception:
                self.devices.setdefault(
                    discovered.ip_address,
                    Device(
                        name=repair_mojibake(discovered.name),
                        ip_address=discovered.ip_address,
                        online=False,
                        reachable=False,
                        service_available=False,
                        source_valid=False,
                        error_text="Gerät gefunden, Dienststatus aktuell nicht abrufbar.",
                    ),
                )
            known_ips.add(discovered.ip_address)
        preferred_ips = self.config_store.load_settings().get("preferred_device_ips", [])
        if isinstance(preferred_ips, list):
            for preferred_ip in preferred_ips:
                ip = str(preferred_ip).strip()
                if not ip or ip in known_ips:
                    continue
                try:
                    self.add_manual_device(ip)
                except Exception:
                    self.devices.setdefault(
                        ip,
                        Device(
                            name=ip,
                            ip_address=ip,
                            online=False,
                            reachable=False,
                            service_available=False,
                            source_valid=False,
                            error_text="Bevorzugte IP gespeichert, Gerät aktuell nicht erreichbar.",
                        ),
                    )
        self.save()
        return self.all_devices()
