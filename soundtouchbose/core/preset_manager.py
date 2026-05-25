"""Preset assignment logic with cache persistence."""

from __future__ import annotations

from typing import Callable

from soundtouchbose.api.client import SoundTouchClient
from soundtouchbose.core.config import ConfigStore
from soundtouchbose.core.station_library import Station


class PresetManager:
    """Assign and cache presets for one or more devices."""

    def __init__(self, config_store: ConfigStore, client_factory: Callable[[str], SoundTouchClient] = SoundTouchClient) -> None:
        self.config_store = config_store
        self.client_factory = client_factory

    def load_cache(self) -> dict[str, dict[str, dict[str, object]]]:
        return self.config_store.load_json("presets.json", {})

    def save_cache(self, payload: dict[str, dict[str, dict[str, object]]]) -> None:
        self.config_store.save_json("presets.json", payload)

    def load_bridge_mappings(self) -> dict[str, dict[str, dict[str, object]]]:
        return self.config_store.load_json("preset_bridge.json", {})

    def save_bridge_mappings(self, payload: dict[str, dict[str, dict[str, object]]]) -> None:
        self.config_store.save_json("preset_bridge.json", payload)

    def assign_bridge_mapping(self, ip_address: str, preset_number: int, station: Station) -> None:
        mappings = self.load_bridge_mappings()
        mappings.setdefault(ip_address, {})[str(preset_number)] = station.to_dict()
        self.save_bridge_mappings(mappings)

    def get_bridge_mappings(self, ip_address: str) -> dict[str, dict[str, object]]:
        return self.load_bridge_mappings().get(ip_address, {})

    def get_bridge_station(self, ip_address: str, preset_number: int) -> Station | None:
        payload = self.get_bridge_mappings(ip_address).get(str(preset_number))
        if not payload:
            return None
        return Station.from_dict(payload)

    def assign_preset(self, ip_address: str, preset_number: int, station: Station) -> bool:
        client = self.client_factory(ip_address)
        ok = client.set_preset(preset_number, station)
        cache = self.load_cache()
        cache.setdefault(ip_address, {})[str(preset_number)] = station.to_dict()
        self.save_cache(cache)
        return ok

    def sync_presets_from_device(self, ip_address: str) -> list[dict[str, object]]:
        client = self.client_factory(ip_address)
        presets = client.get_presets()
        cache = self.load_cache()
        cache[ip_address] = {str(item["id"]): item for item in presets}
        self.save_cache(cache)
        return presets

    def get_cached_presets(self, ip_address: str) -> dict[str, dict[str, object]]:
        return self.load_cache().get(ip_address, {})

    def apply_to_all(self, ip_addresses: list[str], assignments: dict[int, Station]) -> dict[str, list[int]]:
        applied: dict[str, list[int]] = {}
        for ip_address in ip_addresses:
            applied[ip_address] = []
            for preset_number, station in assignments.items():
                if self.assign_preset(ip_address, preset_number, station):
                    applied[ip_address].append(preset_number)
        return applied
