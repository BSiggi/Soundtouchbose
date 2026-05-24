"""Preset editor tab."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from soundtouchbose.core.error_texts import user_error_text
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
        self.device_combo.currentIndexChanged.connect(self.refresh_buttons)
        top_row.addWidget(self.device_combo)
        refresh_devices_button = QPushButton("Geräteliste aktualisieren")
        refresh_devices_button.clicked.connect(self.refresh_devices)
        top_row.addWidget(refresh_devices_button)
        self.bulk_button = QPushButton("Alle 6 Presets auf alle Geräte übertragen")
        self.bulk_button.clicked.connect(self.apply_cached_to_all)
        top_row.addWidget(self.bulk_button)
        layout.addLayout(top_row)
        grid = QGridLayout()
        self.buttons: dict[int, PresetButton] = {}
        for index in range(1, 7):
            button = PresetButton(index)
            button.stationDropped.connect(self.assign_station_to_preset)
            button.clicked.connect(lambda _checked=False, preset=index: self.edit_preset(preset))
            button.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            button.customContextMenuRequested.connect(lambda _pos, preset=index: self.show_menu(preset))
            self.buttons[index] = button
            grid.addWidget(button, (index - 1) // 3, (index - 1) % 3)
        layout.addLayout(grid)
        self.refresh_devices()

    def bridge_enabled(self) -> bool:
        settings = self.services.config_store.load_settings()
        return bool(settings.get("preset_bridge_enabled", False))

    def _update_mode_texts(self) -> None:
        if self.bridge_enabled():
            self.bulk_button.setText("Alle 6 Bridge-Regeln auf alle Geräte übernehmen")
        else:
            self.bulk_button.setText("Alle 6 Presets auf alle Geräte übertragen")

    def refresh_devices(self) -> None:
        self._update_mode_texts()
        current_data = self.device_combo.currentData()
        self.device_combo.clear()
        self.device_combo.addItem("Alle Geräte", None)
        for device in self.services.device_manager.all_devices():
            label = f"{device.name} ({device.ip_address})" if device.name else device.ip_address
            self.device_combo.addItem(label, device.ip_address)
        if current_data:
            index = self.device_combo.findData(current_data)
            if index >= 0:
                self.device_combo.setCurrentIndex(index)
        self.refresh_buttons()

    def set_active_station(self, station_id: str) -> None:
        self.active_station = self.services.station_library.get(station_id)

    def selected_ips(self) -> list[str]:
        selected = self.device_combo.currentData()
        if selected is None:
            return [device.ip_address for device in self.services.device_manager.all_devices()]
        return [str(selected)] if selected else []

    def assign_station_to_preset(self, preset_number: int, station_id: str) -> None:
        station = self.services.station_library.get(station_id)
        if not station:
            QMessageBox.information(self, "Preset", "Der ausgewählte Sender wurde nicht gefunden.")
            return
        errors = []
        bridge_mode = self.bridge_enabled()
        for ip_address in self.selected_ips():
            try:
                if bridge_mode:
                    self.services.preset_manager.assign_bridge_rule(ip_address, preset_number, station)
                else:
                    self.services.preset_manager.assign_preset(ip_address, preset_number, station)
            except Exception as exc:
                errors.append(f"{ip_address}: {user_error_text(exc)}")
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
            if self.bridge_enabled():
                button.setToolTip(
                    "Bridge-Regel: Gerätetaste Preset 1-6 als Trigger nutzen. "
                    "Beim Erkennen startet die App den hier zugeordneten Sender."
                )
            else:
                button.setToolTip("Klicken zum Bearbeiten, Sender aus 'Sender'-Liste hierher ziehen oder Rechtsklick für Aktionen.")
            button.setText(label)

    def edit_preset(self, preset_number: int) -> None:
        ips = self.selected_ips()
        if not ips:
            QMessageBox.information(self, "Preset", "Keine Geräte verfügbar. Bitte zuerst im Reiter 'Geräte' scannen.")
            return
        stations = self.services.station_library.all_stations()
        if not stations:
            QMessageBox.information(self, "Preset", "Keine Sender verfügbar. Bitte zuerst Sender hinzufügen oder importieren.")
            return
        entries = [f"{station.name} ({station.category})" for station in stations]
        selected_label, ok = QInputDialog.getItem(
            self,
            f"Preset {preset_number} {'(Bridge-Regel)' if self.bridge_enabled() else 'bearbeiten'}",
            "Sender auswählen:",
            entries,
            0,
            False,
        )
        if not ok or not selected_label:
            return
        selected_index = entries.index(selected_label)
        self.assign_station_to_preset(preset_number, stations[selected_index].identifier)

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
        errors = []
        for ip_address in self.selected_ips():
            try:
                client = self.services.client_factory(ip_address)
                client.send_key(f"PRESET_{preset_number}", "press")
                client.send_key(f"PRESET_{preset_number}", "release")
            except Exception as exc:
                errors.append(f"{ip_address}: {user_error_text(exc)}")
        if errors:
            QMessageBox.warning(self, "Preset-Test fehlgeschlagen", "\n".join(errors))

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
            if self.bridge_enabled():
                self.services.preset_manager.assign_bridge_rule(device.ip_address, preset_number, station)
            else:
                self.services.preset_manager.assign_preset(device.ip_address, preset_number, station)
        self.refresh_buttons()

    def apply_cached_to_all(self) -> None:
        selected = self.selected_ips()
        if not selected:
            QMessageBox.information(self, "Presets", "Keine Geräte verfügbar.")
            return
        cache = self.services.preset_manager.load_cache().get(selected[0], {})
        if not cache:
            QMessageBox.information(self, "Presets", "Für das ausgewählte Gerät sind keine Presets hinterlegt.")
            return
        assignments = {
            int(preset_number): Station.from_dict(station_payload)
            for preset_number, station_payload in cache.items()
        }
        device_ips = [device.ip_address for device in self.services.device_manager.all_devices()]
        try:
            if self.bridge_enabled():
                for ip_address in device_ips:
                    for preset_number, station in assignments.items():
                        self.services.preset_manager.assign_bridge_rule(ip_address, preset_number, station)
            else:
                self.services.preset_manager.apply_to_all(device_ips, assignments)
        except Exception as exc:
            QMessageBox.warning(self, "Preset-Fehler", user_error_text(exc))
        self.refresh_buttons()
