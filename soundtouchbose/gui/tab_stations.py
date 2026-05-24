"""Station library tab."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDrag, QPixmap
from PySide6.QtCore import QMimeData
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QComboBox,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from soundtouchbose.core.error_texts import user_error_text
from soundtouchbose.services import Services
from soundtouchbose.gui.widgets.station_list_item import StationListItem


class StationListWidget(QListWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setDragEnabled(True)

    def startDrag(self, _supported_actions) -> None:  # noqa: N802
        item = self.currentItem()
        if not isinstance(item, StationListItem):
            return
        drag = QDrag(self)
        mime = QMimeData()
        mime.setText(item.station.identifier)
        drag.setMimeData(mime)
        drag.setPixmap(QPixmap(160, 32))
        drag.exec(Qt.DropAction.CopyAction)


class StationsTab(QWidget):
    stationSelected = Signal(str)

    def __init__(self, services: Services) -> None:
        super().__init__()
        self.services = services
        layout = QVBoxLayout(self)
        filter_row = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Sender suchen …")
        self.search_edit.textChanged.connect(self.refresh_list)
        self.category_combo = QComboBox()
        self.category_combo.currentTextChanged.connect(self.refresh_list)
        self.device_combo = QComboBox()
        self.test_button = QPushButton("Test abspielen")
        self.test_button.clicked.connect(self.test_station)
        self.add_button = QPushButton("Eigenen Sender hinzufügen")
        self.add_button.clicked.connect(self.add_station)
        self.import_button = QPushButton("Import")
        self.import_button.clicked.connect(self.import_stations)
        self.export_button = QPushButton("Export")
        self.export_button.clicked.connect(self.export_stations)
        for widget in (QLabel("Suche:"), self.search_edit, QLabel("Kategorie:"), self.category_combo, QLabel("Gerät:"), self.device_combo):
            filter_row.addWidget(widget)
        layout.addLayout(filter_row)
        action_row = QHBoxLayout()
        for button in (self.test_button, self.add_button, self.import_button, self.export_button):
            action_row.addWidget(button)
        layout.addLayout(action_row)
        self.list_widget = StationListWidget()
        self.list_widget.currentItemChanged.connect(lambda current, _previous: self.stationSelected.emit(current.station.identifier) if isinstance(current, StationListItem) else None)
        layout.addWidget(self.list_widget)
        self.refresh_controls()
        self.refresh_list()

    def refresh_controls(self) -> None:
        categories = ["Alle"] + self.services.station_library.categories()
        self.category_combo.clear()
        self.category_combo.addItems(categories)
        current_data = self.device_combo.currentData()
        self.device_combo.clear()
        for device in self.services.device_manager.all_devices():
            label = f"{device.name} ({device.ip_address})" if device.name else device.ip_address
            self.device_combo.addItem(label, device.ip_address)
        if current_data:
            index = self.device_combo.findData(current_data)
            if index >= 0:
                self.device_combo.setCurrentIndex(index)

    def refresh_list(self) -> None:
        category = self.category_combo.currentText()
        self.list_widget.clear()
        for station in self.services.station_library.search(self.search_edit.text(), None if category in ("", "Alle") else category):
            self.list_widget.addItem(StationListItem(station))

    def selected_station(self):
        item = self.list_widget.currentItem()
        return item.station if isinstance(item, StationListItem) else None

    def test_station(self) -> None:
        station = self.selected_station()
        device_ip = self.device_combo.currentData()
        if not station or not device_ip:
            return
        try:
            self.services.client_factory(device_ip).select(station)
        except Exception as exc:
            QMessageBox.warning(self, "Fehler", f"Testwiedergabe fehlgeschlagen:\n{user_error_text(exc)}")

    def add_station(self) -> None:
        name, ok = QInputDialog.getText(self, "Sendername", "Name:")
        if not ok or not name:
            return
        category, ok = QInputDialog.getText(self, "Kategorie", "Kategorie:", text="Custom")
        if not ok or not category:
            return
        tunein_or_url, ok = QInputDialog.getText(self, "TuneIn oder URL", "TuneIn-ID (s12345) oder Stream-URL:")
        if not ok or not tunein_or_url:
            return
        kwargs = {"tunein_id": tunein_or_url} if tunein_or_url.startswith("s") else {"stream_url": tunein_or_url}
        self.services.station_library.add_station(name, category, **kwargs)
        self.refresh_controls()
        self.refresh_list()

    def export_stations(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Sender exportieren", "stations.json", "JSON (*.json)")
        if not path:
            return
        self.services.station_library.export_json(Path(path))

    def import_stations(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Sender importieren", "", "JSON (*.json)")
        if not path:
            return
        self.services.station_library.import_json(Path(path))
        self.refresh_controls()
        self.refresh_list()
