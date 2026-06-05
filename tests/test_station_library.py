from pathlib import Path

from soundtouchbose.core.config import ConfigStore
from soundtouchbose.core.station_library import StationLibrary


def test_station_library_loads_bundled_stations(tmp_path: Path) -> None:
    library = StationLibrary(ConfigStore(tmp_path))

    stations = library.all_stations()

    assert len(stations) >= 41
    assert any(station.name == "Bayern 1" for station in stations)
    assert any(station.name == "Radio Bob" for station in stations)
    assert any(station.name == "Deutschlandfunk" for station in stations)


def test_station_library_search_filters_by_term_and_category(tmp_path: Path) -> None:
    library = StationLibrary(ConfigStore(tmp_path))

    results = library.search("rock", "Rock")

    assert results
    assert all(station.category == "Rock" for station in results)


def test_station_library_adds_custom_stream_url_station(tmp_path: Path) -> None:
    library = StationLibrary(ConfigStore(tmp_path))

    station = library.add_station("Mein Stream", "Custom", stream_url="https://example.com/radio.mp3")

    assert station.source == "INTERNET_RADIO"
    assert library.get(station.identifier) is not None
    assert library.get(station.identifier).location == "https://example.com/radio.mp3"


def test_station_library_import_export_roundtrip(tmp_path: Path) -> None:
    store = ConfigStore(tmp_path)
    library = StationLibrary(store)
    export_path = tmp_path / "stations-export.json"

    library.export_json(export_path)
    imported = tmp_path / "import.json"
    imported.write_text('[{"identifier":"s999","name":"Test","category":"News","source":"TUNEIN","location":"/v1/playback/station/s999"}]', encoding="utf-8")
    library.import_json(imported)

    assert export_path.exists()
    assert library.get("s999") is not None
