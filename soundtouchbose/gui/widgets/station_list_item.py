"""Station list widget item helper."""

from __future__ import annotations

from PySide6.QtWidgets import QListWidgetItem

from soundtouchbose.core.station_library import Station


class StationListItem(QListWidgetItem):
    def __init__(self, station: Station) -> None:
        super().__init__(f"{station.name} · {station.category}")
        self.station = station
        self.setToolTip(station.location)
