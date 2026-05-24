"""Device discovery and management tab."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from soundtouchbose.services import Services


class DevicesTab(QWidget):
    def __init__(self, services: Services) -> None:
        super().__init__()
        self.services = services
        layout = QVBoxLayout(self)
        button_row = QHBoxLayout()
        self.scan_button = QPushButton("Neu scannen")
        self.scan_button.clicked.connect(self.rescan)
        self.add_button = QPushButton("Manuell hinzufügen")
        self.add_button.clicked.connect(self.add_manual)
        self.remove_button = QPushButton("Entfernen")
        self.remove_button.clicked.connect(self.remove_selected)
        for button in (self.scan_button, self.add_button, self.remove_button):
            button_row.addWidget(button)
        self.table = QTableWidget(0, 10)
        self.table.setHorizontalHeaderLabels(
            ["Name", "IP", "MAC", "Modell", "Firmware", "Quelle", "Rohquelle", "Erreichbar", "Dienst", "Status"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addLayout(button_row)
        layout.addWidget(self.table)
        self.refresh_table()

    def refresh_table(self) -> None:
        devices = self.services.device_manager.all_devices()
        self.table.setRowCount(len(devices))
        for row, device in enumerate(devices):
            values = [
                device.name,
                device.ip_address,
                device.mac_address,
                device.model,
                device.firmware,
                device.source,
                device.source_raw,
                "Ja" if device.reachable else "Nein",
                "Verfügbar" if device.service_available else "Nicht verfügbar",
                device.error_text or ("OK" if device.source_valid else "Quelle prüfen"),
            ]
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(str(value)))

    def rescan(self) -> None:
        self.services.device_manager.rescan()
        self.refresh_table()

    def add_manual(self) -> None:
        ip_address, ok = QInputDialog.getText(self, "Gerät hinzufügen", "IP-Adresse:")
        if not ok or not ip_address:
            return
        try:
            self.services.device_manager.add_manual_device(ip_address)
        except Exception as exc:
            QMessageBox.warning(self, "Fehler", f"Gerät konnte nicht hinzugefügt werden:\n{exc}")
            return
        self.refresh_table()

    def remove_selected(self) -> None:
        current_row = self.table.currentRow()
        if current_row < 0:
            return
        ip_address = self.table.item(current_row, 1).text()
        self.services.device_manager.remove_device(ip_address)
        self.refresh_table()
