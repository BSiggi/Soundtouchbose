"""Station library management."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from importlib.resources import files
from pathlib import Path
from typing import Iterable

from soundtouchbose.core.config import ConfigStore


@dataclass(slots=True)
class Station:
    """Single station entry usable for presets and playback."""

    identifier: str
    name: str
    category: str
    source: str
    location: str
    item_type: str = "stationurl"
    source_account: str = ""
    logo: str = ""
    is_presetable: bool = True

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "Station":
        return cls(
            identifier=str(payload.get("identifier") or payload.get("id") or payload.get("name")),
            name=str(payload["name"]),
            category=str(payload.get("category", "Custom")),
            source=str(payload.get("source", "TUNEIN")),
            location=str(payload.get("location", "")),
            item_type=str(payload.get("item_type", "stationurl")),
            source_account=str(payload.get("source_account", "")),
            logo=str(payload.get("logo", "")),
            is_presetable=bool(payload.get("is_presetable", True)),
        )


class StationLibrary:
    """Load bundled stations and manage user-defined entries."""

    def __init__(self, config_store: ConfigStore) -> None:
        self.config_store = config_store
        self._stations: list[Station] = []
        self.reload()

    def reload(self) -> None:
        bundled_path = files("soundtouchbose.data").joinpath("stations_default.json")
        with bundled_path.open("r", encoding="utf-8") as handle:
            bundled = json.load(handle)
        custom = self.config_store.load_json("stations.json", [])
        stations: dict[str, Station] = {}
        for station in bundled:
            parsed = Station.from_dict(station)
            stations[parsed.identifier] = parsed
        for station in custom:
            parsed = Station.from_dict(station)
            stations[parsed.identifier] = parsed
        self._stations = sorted(stations.values(), key=lambda entry: (entry.category, entry.name.lower()))

    def save_custom(self, stations: Iterable[Station]) -> None:
        payload = [station.to_dict() for station in stations]
        self.config_store.save_json("stations.json", payload)
        self.reload()

    def all_stations(self) -> list[Station]:
        return list(self._stations)

    def categories(self) -> list[str]:
        return sorted({station.category for station in self._stations})

    def search(self, term: str = "", category: str | None = None) -> list[Station]:
        term_normalized = term.strip().lower()
        results = []
        for station in self._stations:
            if category and station.category != category:
                continue
            haystack = f"{station.name} {station.category} {station.location}".lower()
            if term_normalized and term_normalized not in haystack:
                continue
            results.append(station)
        return results

    def get(self, identifier: str) -> Station | None:
        for station in self._stations:
            if station.identifier == identifier:
                return station
        return None

    def add_station(
        self,
        name: str,
        category: str,
        *,
        tunein_id: str | None = None,
        stream_url: str | None = None,
    ) -> Station:
        if bool(tunein_id) == bool(stream_url):
            raise ValueError("Provide either tunein_id or stream_url")
        if tunein_id:
            identifier = tunein_id
            location = f"/v1/playback/station/{tunein_id}"
            source = "TUNEIN"
        else:
            identifier = name.lower().replace(" ", "-")
            location = str(stream_url)
            source = "INTERNET_RADIO"
        station = Station(
            identifier=identifier,
            name=name,
            category=category,
            source=source,
            location=location,
        )
        custom = [item for item in self.config_store.load_json("stations.json", []) if item.get("identifier") != identifier]
        custom.append(station.to_dict())
        self.config_store.save_json("stations.json", custom)
        self.reload()
        return station

    def export_json(self, path: Path) -> Path:
        path.write_text(json.dumps([station.to_dict() for station in self._stations], ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def import_json(self, path: Path) -> None:
        payload = json.loads(path.read_text(encoding="utf-8"))
        merged = [Station.from_dict(entry).to_dict() for entry in payload]
        self.config_store.save_json("stations.json", merged)
        self.reload()
