"""Scheduling tab."""

from __future__ import annotations

from uuid import uuid4

from PySide6.QtCore import QTimer, QTime
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from soundtouchbose.services import Services


class ScheduleTab(QWidget):
    def __init__(self, services: Services) -> None:
        super().__init__()
        self.services = services
        self.sleep_timer: QTimer | None = None
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.time_edit = QTimeEdit(QTime.currentTime())
        self.device_combo = QComboBox()
        self.device_combo.addItems([device.ip_address for device in self.services.device_manager.all_devices()])
        self.action_combo = QComboBox()
        self.action_combo.addItems([("Sender starten"), ("Aus"), ("Lautstärke setzen")])
        self.station_combo = QComboBox()
        self.station_combo.addItems([station.identifier for station in self.services.station_library.all_stations()])
        self.volume_spin = QSpinBox()
        self.volume_spin.setRange(0, 100)
        self.volume_spin.setValue(20)
        form.addRow("Zeit", self.time_edit)
        form.addRow("Gerät", self.device_combo)
        form.addRow("Aktion", self.action_combo)
        form.addRow("Sender", self.station_combo)
        form.addRow("Lautstärke", self.volume_spin)
        weekday_row = QHBoxLayout()
        self.day_checks = []
        for label in ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]:
            checkbox = QCheckBox(label)
            checkbox.setChecked(True)
            self.day_checks.append(checkbox)
            weekday_row.addWidget(checkbox)
        add_button = QPushButton("Neuen Plan speichern")
        add_button.clicked.connect(self.add_schedule)
        self.list_widget = QListWidget()
        delete_button = QPushButton("Ausgewählten Plan löschen")
        delete_button.clicked.connect(self.remove_schedule)
        sleep_row = QHBoxLayout()
        self.sleep_spin = QSpinBox()
        self.sleep_spin.setRange(1, 180)
        self.sleep_spin.setValue(30)
        self.sleep_button = QPushButton("Sleep-Timer starten")
        self.sleep_button.clicked.connect(self.start_sleep_timer)
        sleep_row.addWidget(QLabel("Alle Geräte aus in Minuten:"))
        sleep_row.addWidget(self.sleep_spin)
        sleep_row.addWidget(self.sleep_button)
        layout.addLayout(form)
        layout.addLayout(weekday_row)
        layout.addWidget(add_button)
        layout.addWidget(self.list_widget)
        layout.addWidget(delete_button)
        layout.addLayout(sleep_row)
        self.refresh_list()

    def refresh_list(self) -> None:
        self.list_widget.clear()
        for item in self.services.scheduler.load_definitions():
            self.list_widget.addItem(f"{item['id']} · {item['time']} · {item['action']} · {','.join(item['devices'])}")

    def add_schedule(self) -> None:
        action_map = {"Sender starten": "station", "Aus": "power_off", "Lautstärke setzen": "volume"}
        definition = {
            "id": str(uuid4()),
            "time": self.time_edit.time().toString("HH:mm"),
            "days": [checkbox.isChecked() for checkbox in self.day_checks],
            "devices": [self.device_combo.currentText()],
            "action": action_map[self.action_combo.currentText()],
            "station_id": self.station_combo.currentText(),
            "volume": self.volume_spin.value(),
            "enabled": True,
        }
        self.services.scheduler.add_definition(definition)
        self.refresh_list()

    def remove_schedule(self) -> None:
        item = self.list_widget.currentItem()
        if not item:
            return
        definition_id = item.text().split(" · ", 1)[0]
        try:
            self.services.scheduler.remove_definition(definition_id)
        except Exception as exc:
            QMessageBox.warning(self, "Zeitplan-Fehler", str(exc))
        self.refresh_list()

    def start_sleep_timer(self) -> None:
        if self.sleep_timer:
            self.sleep_timer.stop()
        self.sleep_timer = QTimer(self)
        self.sleep_timer.setSingleShot(True)
        self.sleep_timer.timeout.connect(self.turn_off_all)
        self.sleep_timer.start(self.sleep_spin.value() * 60 * 1000)

    def turn_off_all(self) -> None:
        for device in self.services.device_manager.all_devices():
            self.services.client_factory(device.ip_address).power("off")
