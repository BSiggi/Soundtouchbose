"""Settings tab."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QCheckBox,
    QLabel,
    QSpinBox,
    QWidget,
)

from soundtouchbose import __version__
from soundtouchbose.core.error_texts import user_error_text
from soundtouchbose.runtime import sync_autostart
from soundtouchbose.services import Services


class SettingsTab(QWidget):
    def __init__(self, services: Services) -> None:
        super().__init__()
        self.services = services
        self.settings = self.services.config_store.load_settings()
        layout = QFormLayout(self)
        self.version_label = QLabel(self.settings.get("installed_version", __version__))
        layout.addRow("Version", self.version_label)
        self.autostart = QCheckBox()
        self.autostart.setChecked(self.settings.get("autostart", False))
        self.minimize_to_tray = QCheckBox()
        self.minimize_to_tray.setChecked(self.settings.get("minimize_to_tray", True))
        self.web_enabled = QCheckBox()
        self.web_enabled.setChecked(self.settings.get("web_ui_enabled", True))
        self.web_port = QSpinBox()
        self.web_port.setRange(1024, 65535)
        self.web_port.setValue(int(self.settings.get("web_ui_port", 8765)))
        self.ha_enabled = QCheckBox()
        self.ha_enabled.setChecked(self.settings.get("home_assistant_enabled", False))
        self.ha_port = QSpinBox()
        self.ha_port.setRange(1024, 65535)
        self.ha_port.setValue(int(self.settings.get("home_assistant_port", 8766)))
        self.ha_token = QLineEdit(self.settings.get("home_assistant_token", "change-me"))
        self.night_mode = QCheckBox()
        self.night_mode.setChecked(self.settings.get("night_mode_enabled", False))
        self.night_volume = QSpinBox()
        self.night_volume.setRange(0, 100)
        self.night_volume.setValue(int(self.settings.get("night_mode_max_volume", 20)))
        preferred_ips = self.settings.get("preferred_device_ips", [])
        preferred_ips_entries = []
        if isinstance(preferred_ips, list):
            preferred_ips_entries = [str(item).strip() for item in preferred_ips if str(item).strip()]
        preferred_ips_text = ", ".join(preferred_ips_entries)
        self.preferred_ips = QLineEdit(preferred_ips_text)
        self.preferred_ips.setPlaceholderText("z. B. 192.168.100.148, 192.168.100.111")
        self.eol_hint = QLabel(
            "Bose SoundTouch EOL-Hinweis: Echtes Überschreiben/Löschen von Geräte-Presets kann vom Gerät abgelehnt werden. "
            "Die App speichert Favoriten lokal und versucht zusätzlich den Geräteschreibzugriff."
        )
        self.eol_hint.setWordWrap(True)
        layout.addRow("Mit Windows starten", self.autostart)
        layout.addRow("Im Tray minimieren", self.minimize_to_tray)
        layout.addRow("Mini-Web-UI aktiv", self.web_enabled)
        layout.addRow("Mini-Web-UI Port", self.web_port)
        layout.addRow("Home Assistant Bridge aktiv", self.ha_enabled)
        layout.addRow("Home Assistant Port", self.ha_port)
        layout.addRow("Home Assistant Token", self.ha_token)
        layout.addRow("Nachtmodus aktiv", self.night_mode)
        layout.addRow("Nachtmodus Max-Lautstärke", self.night_volume)
        layout.addRow("Bevorzugte Geräte-IPs", self.preferred_ips)
        layout.addRow("Hinweis", self.eol_hint)
        action_row = QHBoxLayout()
        save_button = QPushButton("Speichern")
        save_button.clicked.connect(self.save_settings)
        export_button = QPushButton("Backup exportieren")
        export_button.clicked.connect(self.export_backup)
        restore_button = QPushButton("Backup importieren")
        restore_button.clicked.connect(self.import_backup)
        update_button = QPushButton("Update anwenden …")
        update_button.clicked.connect(self.apply_update)
        diagnostics_button = QPushButton("Diagnose exportieren")
        diagnostics_button.clicked.connect(self.export_diagnostics)
        cleanup_button = QPushButton("Cleanup ausführen")
        cleanup_button.clicked.connect(self.run_cleanup)
        action_row.addWidget(save_button)
        action_row.addWidget(export_button)
        action_row.addWidget(restore_button)
        action_row.addWidget(update_button)
        action_row.addWidget(diagnostics_button)
        action_row.addWidget(cleanup_button)
        layout.addRow(action_row)

    def save_settings(self) -> None:
        settings = {
            "autostart": self.autostart.isChecked(),
            "minimize_to_tray": self.minimize_to_tray.isChecked(),
            "web_ui_enabled": self.web_enabled.isChecked(),
            "web_ui_port": self.web_port.value(),
            "home_assistant_enabled": self.ha_enabled.isChecked(),
            "home_assistant_port": self.ha_port.value(),
            "home_assistant_token": self.ha_token.text().strip() or "change-me",
            "night_mode_enabled": self.night_mode.isChecked(),
            "night_mode_max_volume": self.night_volume.value(),
            "preferred_device_ips": [entry.strip() for entry in self.preferred_ips.text().split(",") if entry.strip()],
        }
        self.services.config_store.save_settings(settings)
        sync_autostart(self.autostart.isChecked())
        QMessageBox.information(self, "Gespeichert", "Einstellungen gespeichert. Für Port-Änderungen die App bitte neu starten.")

    def export_backup(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Backup exportieren", "soundtouchbose-backup.zip", "ZIP (*.zip)")
        if path:
            self.services.config_store.backup_to_zip(Path(path))

    def import_backup(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Backup importieren", "", "ZIP (*.zip)")
        if path:
            self.services.config_store.restore_from_zip(Path(path))
            QMessageBox.information(self, "Importiert", "Backup wurde wiederhergestellt.")

    def apply_update(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Update-Datei auswählen", "", "ZIP (*.zip)")
        if not path:
            return
        try:
            result = self.services.update_manager.apply_update_package(Path(path))
        except Exception as exc:
            QMessageBox.warning(self, "Update fehlgeschlagen", user_error_text(exc))
            return
        self.settings = self.services.config_store.load_settings()
        self.version_label.setText(result.package_version or self.settings.get("installed_version", __version__))
        QMessageBox.information(
            self,
            "Update angewendet",
            f"Backup erstellt: {result.backup_path}\nAktualisierte Dateien: {len(result.applied_files)}",
        )

    def export_diagnostics(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Diagnose exportieren",
            "soundtouchbose-diagnose.zip",
            "ZIP (*.zip)",
        )
        if not path:
            return
        try:
            report_path = self.services.diagnostics_service.export(Path(path))
        except Exception as exc:
            QMessageBox.warning(self, "Diagnose fehlgeschlagen", user_error_text(exc))
            return
        QMessageBox.information(self, "Diagnose exportiert", f"Datei erstellt:\n{report_path}")

    def run_cleanup(self) -> None:
        if QMessageBox.question(
            self,
            "Cleanup ausführen",
            "Autostart entfernen, alte Backups bereinigen und bekannte Dienste stoppen?",
        ) != QMessageBox.StandardButton.Yes:
            return
        result = self.services.cleanup_service.run_cleanup()
        services = result.get("service_status") or {}
        QMessageBox.information(
            self,
            "Cleanup abgeschlossen",
            f"Entfernte Backups: {len(result.get('removed_backups', []))}\n"
            f"Dienststatus: {services or 'Keine Dienste gefunden'}",
        )
