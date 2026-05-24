"""Zone and multi-room group helpers."""

from __future__ import annotations

from typing import Callable

from soundtouchbose.api.client import SoundTouchClient
from soundtouchbose.core.config import ConfigStore


class ZoneManager:
    def __init__(self, config_store: ConfigStore, client_factory: Callable[[str], SoundTouchClient] = SoundTouchClient) -> None:
        self.config_store = config_store
        self.client_factory = client_factory

    def load_groups(self) -> list[dict[str, object]]:
        return self.config_store.load_json("zones.json", [])

    def save_groups(self, groups: list[dict[str, object]]) -> None:
        self.config_store.save_json("zones.json", groups)

    def create_zone(self, master_ip: str, members: list[str]) -> None:
        self.client_factory(master_ip).set_zone(master_ip, members)

    def remove_zone(self, master_ip: str) -> None:
        self.client_factory(master_ip).remove_zone(master_ip)

    def save_group(self, name: str, master_ip: str, members: list[str]) -> None:
        groups = [group for group in self.load_groups() if group.get("name") != name]
        groups.append({"name": name, "master_ip": master_ip, "members": members})
        self.save_groups(groups)
