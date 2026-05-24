"""Zone management tab."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from soundtouchbose.services import Services


class ZonesTab(QWidget):
    def __init__(self, services: Services) -> None:
        super().__init__()
        self.services = services
        layout = QVBoxLayout(self)
        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("Master:"))
        self.master_combo = QComboBox()
        top_row.addWidget(self.master_combo)
        self.create_button = QPushButton("Zone erstellen")
        self.create_button.clicked.connect(self.create_zone)
        self.remove_button = QPushButton("Zone auflösen")
        self.remove_button.clicked.connect(self.remove_zone)
        self.save_button = QPushButton("Gruppe speichern")
        self.save_button.clicked.connect(self.save_group)
        for button in (self.create_button, self.remove_button, self.save_button):
            top_row.addWidget(button)
        layout.addLayout(top_row)
        self.device_checks: list[QCheckBox] = []
        for device in self.services.device_manager.all_devices():
            checkbox = QCheckBox(f"{device.name} ({device.ip_address})")
            checkbox.setProperty("ip_address", device.ip_address)
            self.device_checks.append(checkbox)
            layout.addWidget(checkbox)
        self.group_list = QListWidget()
        self.group_list.itemDoubleClicked.connect(lambda item: self.apply_group(item.text()))
        self.apply_button = QPushButton("Gespeicherte Gruppe aktivieren")
        self.apply_button.clicked.connect(lambda: self.apply_group(self.group_list.currentItem().text() if self.group_list.currentItem() else ""))
        layout.addWidget(self.group_list)
        layout.addWidget(self.apply_button)
        self.refresh_controls()

    def refresh_controls(self) -> None:
        self.master_combo.clear()
        self.master_combo.addItems([device.ip_address for device in self.services.device_manager.all_devices()])
        self.group_list.clear()
        for group in self.services.zone_manager.load_groups():
            self.group_list.addItem(str(group.get("name")))

    def selected_members(self) -> list[str]:
        return [str(checkbox.property("ip_address")) for checkbox in self.device_checks if checkbox.isChecked()]

    def create_zone(self) -> None:
        try:
            self.services.zone_manager.create_zone(self.master_combo.currentText(), self.selected_members())
        except Exception as exc:
            QMessageBox.warning(self, "Zone-Fehler", str(exc))

    def remove_zone(self) -> None:
        self.services.zone_manager.remove_zone(self.master_combo.currentText())

    def save_group(self) -> None:
        name, ok = QInputDialog.getText(self, "Gruppenname", "Name:")
        if ok and name:
            self.services.zone_manager.save_group(name, self.master_combo.currentText(), self.selected_members())
            self.refresh_controls()

    def apply_group(self, name: str) -> None:
        for group in self.services.zone_manager.load_groups():
            if group.get("name") == name:
                self.services.zone_manager.create_zone(str(group.get("master_ip")), list(group.get("members", [])))
                break
