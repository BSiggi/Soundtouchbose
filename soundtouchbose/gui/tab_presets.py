"""Preset editor tab."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QGridLayout, QHBoxLayout, QLabel, QMenu, QMessageBox, QPushButton, QVBoxLayout, QWidget

from soundtouchbose.services import Services
from soundtouchbose.core.station_library import Station
from soundtouchbose.gui.widgets.preset_button import PresetButton


class PresetsTab(QWidget):
    def __init__(self, services: Services) -> None:
        super().__init__()
        self.services = services
        self.active_station: Station | None = None
        layout = QVBoxLayout(self)
        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("Gerät:"))
        self.device_combo = QComboBox()
        self.device_combo.currentTextChanged.connect(self.refresh_buttons)
        top_row.addWidget(self.device_combo)
        self.bulk_button = QPushButton("Alle 6 Presets auf alle Geräte übertragen")
        self.bulk_button.clicked.connect(self.apply_cached_to_all)
        top_row.addWidget(self.bulk_button)
        layout.addLayout(top_row)
        grid = QGridLayout()
        self.buttons: dict[int, PresetButton] = {}
        for index in range(1, 7):
            button = PresetButton(index)
            button.stationDropped.connect(self.assign_station_to_preset)
            button.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            button.customContextMenuRequested.connect(lambda _pos, preset=index: self.show_menu(preset))
            self.buttons[index] = button
            grid.addWidget(button, (index - 1) // 3, (index - 1) % 3)
        layout.addLayout(grid)
        self.refresh_devices()

    def refresh_devices(self) -> None:
        current = self.device_combo.currentText()
        self.device_combo.clear()
        self.device_combo.addItem("Alle Geräte")
        self.device_combo.addItems([device.ip_address for device in self.services.device_manager.all_devices()])
        if current:
            index = self.device_combo.findText(current)
            if index >= 0:
                self.device_combo.setCurrentIndex(index)
        self.refresh_buttons()

    def set_active_station(self, station_id: str) -> None:
        self.active_station = self.services.station_library.get(station_id)

    def selected_ips(self) -> list[str]:
        selected = self.device_combo.currentText()
        if selected == "Alle Geräte":
            return [device.ip_address for device in self.services.device_manager.all_devices()]
        return [selected] if selected else []

    def assign_station_to_preset(self, preset_number: int, station_id: str) -> None:
        station = self.services.station_library.get(station_id)
        if not station:
            return
        errors = []
        for ip_address in self.selected_ips():
            try:
                self.services.preset_manager.assign_preset(ip_address, preset_number, station)
            except Exception as exc:
                errors.append(f"{ip_address}: {exc}")
        self.active_station = station
        self.refresh_buttons()
        if errors:
            QMessageBox.warning(self, "Preset-Fehler", "\n".join(errors))

    def refresh_buttons(self) -> None:
        ips = self.selected_ips()
        cache = self.services.preset_manager.load_cache()
        for preset_number, button in self.buttons.items():
            label = f"Preset {preset_number}\nNicht belegt"
            if ips:
                station_payload = cache.get(ips[0], {}).get(str(preset_number))
                if station_payload:
                    label = f"Preset {preset_number}\n{station_payload.get('name', station_payload.get('item_name', 'Unbekannt'))}"
            button.setText(label)

    def show_menu(self, preset_number: int) -> None:
        menu = QMenu(self)
        clear_action = menu.addAction("Löschen")
        test_action = menu.addAction("Testen")
        apply_all_action = menu.addAction("Auf alle Geräte übernehmen")
        chosen = menu.exec(self.cursor().pos())
        if chosen == clear_action:
            cache = self.services.preset_manager.load_cache()
            for ip_address in self.selected_ips():
                cache.setdefault(ip_address, {}).pop(str(preset_number), None)
            self.services.preset_manager.save_cache(cache)
            self.refresh_buttons()
        elif chosen == test_action:
            self.test_preset(preset_number)
        elif chosen == apply_all_action:
            self.apply_single_to_all(preset_number)

    def test_preset(self, preset_number: int) -> None:
        for ip_address in self.selected_ips():
            client = self.services.client_factory(ip_address)
            client.send_key(f"PRESET_{preset_number}", "press")
            client.send_key(f"PRESET_{preset_number}", "release")

    def apply_single_to_all(self, preset_number: int) -> None:
        selected = self.selected_ips()
        if not selected:
            return
        cache = self.services.preset_manager.load_cache()
        station_payload = cache.get(selected[0], {}).get(str(preset_number))
        if not station_payload:
            return
        station = Station.from_dict(station_payload)
        for device in self.services.device_manager.all_devices():
            self.services.preset_manager.assign_preset(device.ip_address, preset_number, station)
        self.refresh_buttons()

    def apply_cached_to_all(self) -> None:
        selected = self.selected_ips()
        if not selected:
            return
        cache = self.services.preset_manager.load_cache().get(selected[0], {})
        assignments = {
            int(preset_number): Station.from_dict(station_payload)
            for preset_number, station_payload in cache.items()
        }
        device_ips = [device.ip_address for device in self.services.device_manager.all_devices()]
        self.services.preset_manager.apply_to_all(device_ips, assignments)
        self.refresh_buttons()
