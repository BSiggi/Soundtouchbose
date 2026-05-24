"""Application bootstrap for SoundTouchBose."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
import sys
import threading
from pathlib import Path

from PySide6.QtGui import QAction, QCloseEvent, QIcon
from PySide6.QtWidgets import QApplication, QMainWindow, QMenu, QMessageBox, QSystemTrayIcon

from soundtouchbose import __version__
from soundtouchbose.api.client import SoundTouchClient
from soundtouchbose.core.cleanup_service import CleanupService
from soundtouchbose.core.config import ConfigStore
from soundtouchbose.core.diagnostics_service import DiagnosticsService
from soundtouchbose.core.device_manager import DeviceManager
from soundtouchbose.core.preset_bridge import PresetBridgeService
from soundtouchbose.core.preset_manager import PresetManager
from soundtouchbose.core.scheduler import SchedulerService
from soundtouchbose.core.station_library import StationLibrary
from soundtouchbose.core.update_manager import UpdateManager
from soundtouchbose.core.zone_manager import ZoneManager
from soundtouchbose.runtime import resource_path
from soundtouchbose.services import Services

LOGGER = logging.getLogger(__name__)


class SoundTouchBoseApplication(QMainWindow):
    def __init__(self, services: Services) -> None:
        super().__init__()
        self.services = services
        self.settings = services.config_store.load_settings()
        self.setWindowTitle(f"SoundTouchBose {self.settings.get('installed_version', __version__)}")
        self.setMinimumSize(1280, 820)
        icon_path = resource_path("icon.png")
        self.setWindowIcon(QIcon(str(icon_path)))
        from soundtouchbose.gui.main_window import MainWindow

        self.main_window = MainWindow(services)
        self.setCentralWidget(self.main_window)
        self.tray_icon = self._create_tray_icon()
        self._server_threads: list[threading.Thread] = []
        self.services.preset_bridge_service.start()
        self._start_optional_servers()

    def _create_tray_icon(self) -> QSystemTrayIcon:
        tray = QSystemTrayIcon(QIcon(str(resource_path("icon.png"))), self)
        tray.setToolTip("SoundTouchBose")
        menu = QMenu(self)
        show_action = QAction("Hauptfenster zeigen", self)
        show_action.triggered.connect(self.showNormal)
        mute_action = QAction("Alle Geräte stumm", self)
        mute_action.triggered.connect(lambda: self._set_all_volumes(0))
        off_action = QAction("Alle aus", self)
        off_action.triggered.connect(self._power_off_all)
        quit_action = QAction("Beenden", self)
        quit_action.triggered.connect(self.exit_application)
        for action in (show_action, mute_action, off_action, quit_action):
            menu.addAction(action)
        tray.setContextMenu(menu)
        tray.activated.connect(lambda reason: self.showNormal() if reason == QSystemTrayIcon.ActivationReason.DoubleClick else None)
        tray.show()
        return tray

    def _set_all_volumes(self, volume: int) -> None:
        for device in self.services.device_manager.all_devices():
            if device.ip_address:
                self.services.client_factory(device.ip_address).set_volume(volume)

    def _power_off_all(self) -> None:
        for device in self.services.device_manager.all_devices():
            if device.ip_address:
                self.services.client_factory(device.ip_address).power("off")

    def _start_optional_servers(self) -> None:
        settings = self.settings
        if settings.get("web_ui_enabled", True):
            from soundtouchbose.web.server import create_web_app, run_waitress as run_web_waitress

            web_app = create_web_app(self.services)
            thread = threading.Thread(
                target=run_web_waitress,
                kwargs={"app": web_app, "port": int(settings.get("web_ui_port", 8765))},
                daemon=True,
            )
            thread.start()
            self._server_threads.append(thread)
        if settings.get("home_assistant_enabled", False):
            from soundtouchbose.integrations.homeassistant import create_homeassistant_app, run_waitress as run_homeassistant_waitress

            ha_app = create_homeassistant_app(self.services)
            thread = threading.Thread(
                target=run_homeassistant_waitress,
                kwargs={"app": ha_app, "host": "127.0.0.1", "port": int(settings.get("home_assistant_port", 8766))},
                daemon=True,
            )
            thread.start()
            self._server_threads.append(thread)

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        if self.settings.get("minimize_to_tray", True):
            self.hide()
            self.tray_icon.showMessage("SoundTouchBose", "Die Anwendung läuft weiter im Tray.")
            event.ignore()
            return
        super().closeEvent(event)

    def exit_application(self) -> None:
        self.services.scheduler.shutdown()
        self.services.preset_bridge_service.stop()
        self.tray_icon.hide()
        QApplication.instance().quit()


def configure_logging(config_store: ConfigStore) -> None:
    log_path = config_store.logs_dir / "app.log"
    handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()
    root.addHandler(handler)
    root.addHandler(logging.StreamHandler(sys.stdout))


def create_services(config_dir: Path | None = None) -> Services:
    config_store = ConfigStore(config_dir)
    client_factory = SoundTouchClient
    station_library = StationLibrary(config_store)
    device_manager = DeviceManager(config_store, client_factory)
    update_manager = UpdateManager(config_store, Path(__file__).resolve().parents[1], __version__)
    preset_manager = PresetManager(config_store, client_factory)
    services = Services(
        config_store=config_store,
        device_manager=device_manager,
        station_library=station_library,
        preset_manager=preset_manager,
        zone_manager=ZoneManager(config_store, client_factory),
        scheduler=SchedulerService(config_store, station_library, client_factory),
        update_manager=update_manager,
        diagnostics_service=DiagnosticsService(),
        cleanup_service=CleanupService(config_store),
        preset_bridge_service=PresetBridgeService(
            config_store=config_store,
            device_manager=device_manager,
            preset_manager=preset_manager,
            station_library=station_library,
            client_factory=client_factory,
        ),
        client_factory=client_factory,
    )
    services.diagnostics_service.services = services
    return services


def main() -> None:
    services = create_services()
    configure_logging(services.config_store)
    services.scheduler.start()
    app = QApplication(sys.argv)
    window = SoundTouchBoseApplication(services)
    window.show()
    app.exec()


__all__ = ["SoundTouchBoseApplication", "create_services", "main"]
