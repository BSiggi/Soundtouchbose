"""Zeroconf device discovery for SoundTouch devices."""

from __future__ import annotations

import socket
import time
from dataclasses import dataclass
from typing import Callable

from zeroconf import ServiceBrowser, ServiceListener, Zeroconf


@dataclass(slots=True)
class DiscoveredDevice:
    name: str
    ip_address: str
    port: int
    server: str


class _Listener(ServiceListener):
    def __init__(self, zeroconf: Zeroconf, callback: Callable[[DiscoveredDevice], None]) -> None:
        self.zeroconf = zeroconf
        self.callback = callback

    def add_service(self, zeroconf: Zeroconf, service_type: str, name: str) -> None:
        self._handle(name)

    def update_service(self, zeroconf: Zeroconf, service_type: str, name: str) -> None:
        self._handle(name)

    def remove_service(self, zeroconf: Zeroconf, service_type: str, name: str) -> None:  # pragma: no cover - UI only
        return None

    def _handle(self, name: str) -> None:
        info = self.zeroconf.get_service_info("_soundtouch._tcp.local.", name)
        if not info or not info.addresses:
            return
        address = socket.inet_ntoa(info.addresses[0])
        device = DiscoveredDevice(name=name.replace("._soundtouch._tcp.local.", ""), ip_address=address, port=info.port, server=info.server)
        self.callback(device)


def discover_once(timeout: float = 3.0) -> list[DiscoveredDevice]:
    zeroconf = Zeroconf()
    discovered: dict[str, DiscoveredDevice] = {}
    listener = _Listener(zeroconf, lambda device: discovered.__setitem__(device.ip_address, device))
    ServiceBrowser(zeroconf, "_soundtouch._tcp.local.", listener)
    time.sleep(timeout)
    zeroconf.close()
    return list(discovered.values())
