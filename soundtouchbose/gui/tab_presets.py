"""Preset editor tab."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
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
        self.bridge_info = QLabel("")
        self.bridge_info.setWordWrap(True)
        layout.addWidget(self.bridge_info)
        self.bridge_status = QLabel("")
        self.bridge_status.setWordWrap(True)
        layout.addWidget(self.bridge_status)
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
        self.bridge_status_timer = QTimer(self)
        self.bridge_status_timer.timeout.connect(self.refresh_bridge_status)
        self.bridge_status_timer.start(2_000)

    def refresh_devices(self) -> None:
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
        bridge_enabled = bool(self.services.config_store.load_settings().get("preset_bridge_enabled", False))
        errors = []
        for ip_address in self.selected_ips():
            try:
                if bridge_enabled:
                    self.services.preset_manager.assign_bridge_mapping(ip_address, preset_number, station)
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
        bridge_enabled = bool(self.services.config_store.load_settings().get("preset_bridge_enabled", False))
        cache = (
            self.services.preset_manager.load_bridge_mappings()
            if bridge_enabled
            else self.services.preset_manager.load_cache()
        )
        if bridge_enabled:
            self.bridge_info.setText(
                "Preset-Bridge ist aktiv: Die Tasten 1–6 am Bose-Gerät werden nur als Auslöser genutzt. "
                "Die Zuordnung ist lokal in dieser App gespeichert und überschreibt keine Bose-Presets. "
                "Nach dem Test: 'Einstellungen' → 'Diagnose exportieren'."
            )
        else:
            self.bridge_info.setText(
                "Preset-Bridge ist deaktiviert. Zum Troubleshooting nach dem Test: "
                "'Einstellungen' → 'Diagnose exportieren'."
            )
        self.refresh_bridge_status()
        for preset_number, button in self.buttons.items():
            label = f"Preset {preset_number}\nNicht belegt"
            if ips:
                station_payload = cache.get(ips[0], {}).get(str(preset_number))
                if station_payload:
                    label = f"Preset {preset_number}\n{station_payload.get('name', station_payload.get('item_name', 'Unbekannt'))}"
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
            f"Preset {preset_number} bearbeiten",
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
            bridge_enabled = bool(self.services.config_store.load_settings().get("preset_bridge_enabled", False))
            cache = (
                self.services.preset_manager.load_bridge_mappings()
                if bridge_enabled
                else self.services.preset_manager.load_cache()
            )
            for ip_address in self.selected_ips():
                cache.setdefault(ip_address, {}).pop(str(preset_number), None)
            if bridge_enabled:
                self.services.preset_manager.save_bridge_mappings(cache)
            else:
                self.services.preset_manager.save_cache(cache)
            self.refresh_buttons()
        elif chosen == test_action:
            self.test_preset(preset_number)
        elif chosen == apply_all_action:
            self.apply_single_to_all(preset_number)

    def test_preset(self, preset_number: int) -> None:
        errors = []
        bridge_enabled = bool(self.services.config_store.load_settings().get("preset_bridge_enabled", False))
        for ip_address in self.selected_ips():
            try:
                if bridge_enabled:
                    station = self.services.preset_manager.get_bridge_station(ip_address, preset_number)
                    if station:
                        self.services.client_factory(ip_address).select(station)
                    else:
                        errors.append(f"{ip_address}: Keine lokale Preset-Bridge-Zuordnung für Preset {preset_number}.")
                else:
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
        bridge_enabled = bool(self.services.config_store.load_settings().get("preset_bridge_enabled", False))
        if bridge_enabled:
            cache = self.services.preset_manager.load_bridge_mappings()
        station_payload = cache.get(selected[0], {}).get(str(preset_number))
        if not station_payload:
            return
        station = Station.from_dict(station_payload)
        for device in self.services.device_manager.all_devices():
            if bridge_enabled:
                self.services.preset_manager.assign_bridge_mapping(device.ip_address, preset_number, station)
            else:
                self.services.preset_manager.assign_preset(device.ip_address, preset_number, station)
        self.refresh_buttons()

    def apply_cached_to_all(self) -> None:
        selected = self.selected_ips()
        if not selected:
            QMessageBox.information(self, "Presets", "Keine Geräte verfügbar.")
            return
        bridge_enabled = bool(self.services.config_store.load_settings().get("preset_bridge_enabled", False))
        cache = (
            self.services.preset_manager.load_bridge_mappings().get(selected[0], {})
            if bridge_enabled
            else self.services.preset_manager.load_cache().get(selected[0], {})
        )
        if not cache:
            QMessageBox.information(self, "Presets", "Für das ausgewählte Gerät sind keine Presets hinterlegt.")
            return
        assignments = {
            int(preset_number): Station.from_dict(station_payload)
            for preset_number, station_payload in cache.items()
        }
        try:
            if bridge_enabled:
                for device in self.services.device_manager.all_devices():
                    for preset_number, station in assignments.items():
                        self.services.preset_manager.assign_bridge_mapping(device.ip_address, preset_number, station)
            else:
                device_ips = [device.ip_address for device in self.services.device_manager.all_devices()]
                self.services.preset_manager.apply_to_all(device_ips, assignments)
        except Exception as exc:
            QMessageBox.warning(self, "Preset-Fehler", user_error_text(exc))
        self.refresh_buttons()

    def refresh_bridge_status(self) -> None:
        ips = self.selected_ips()
        if not ips:
            self.bridge_status.setText("")
            return
        device_names = {
            device.ip_address: (f"{device.name} ({device.ip_address})" if device.name else device.ip_address)
            for device in self.services.device_manager.all_devices()
        }
        lines = []
        for ip_address in ips:
            status = self.services.preset_bridge.get_device_status(ip_address)
            lines.append(
                f"{device_names.get(ip_address, ip_address)}: "
                f"Bridge {'an' if status.get('bridge_enabled') else 'aus'} | "
                f"Zuordnungen {status.get('mapping_count', 0)} | "
                f"Trigger {self._format_bridge_trigger(status)} | "
                f"Start {self._format_bridge_launch(status)}"
            )
        self.bridge_status.setText("\n".join(lines))

    @staticmethod
    def _format_bridge_trigger(status: dict[str, object]) -> str:
        trigger = status.get("last_trigger") or {}
        if not isinstance(trigger, dict) or not trigger.get("detected"):
            return "noch keiner erkannt"
        mode = str(trigger.get("mode") or "unknown")
        preset_number = trigger.get("preset_number")
        return f"Preset {preset_number} ({mode})"

    @staticmethod
    def _format_bridge_launch(status: dict[str, object]) -> str:
        launch = status.get("last_launch") or {}
        if not isinstance(launch, dict):
            return "noch kein Startversuch"
        result = str(launch.get("result") or "idle")
        station_name = str(launch.get("station_name") or "").strip()
        if result == "succeeded":
            return f"erfolgreich → {station_name or 'unbekannt'}"
        if result == "failed":
            error = str(launch.get("error") or "").strip()
            return f"fehlgeschlagen → {station_name or 'unbekannt'} ({error or 'unbekannter Fehler'})"
        if result == "no_mapping":
            return "kein lokales Mapping vorhanden"
        if result == "bridge_disabled":
            return "Bridge deaktiviert"
        return "noch kein Startversuch"
