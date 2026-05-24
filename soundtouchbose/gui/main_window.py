"""Main application window."""

from __future__ import annotations

from importlib.resources import files

from PySide6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from soundtouchbose.services import Services
from soundtouchbose.gui.tab_dashboard import DashboardTab
from soundtouchbose.gui.tab_devices import DevicesTab
from soundtouchbose.gui.tab_presets import PresetsTab
from soundtouchbose.gui.tab_schedule import ScheduleTab
from soundtouchbose.gui.tab_settings import SettingsTab
from soundtouchbose.gui.tab_stations import StationsTab
from soundtouchbose.gui.tab_zones import ZonesTab


class MainWindow(QWidget):
    def __init__(self, services: Services) -> None:
        super().__init__()
        self.services = services
        qss_path = files("soundtouchbose.gui").joinpath("style.qss")
        self.setStyleSheet(qss_path.read_text(encoding="utf-8"))
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.devices_tab = DevicesTab(services)
        self.stations_tab = StationsTab(services)
        self.presets_tab = PresetsTab(services)
        self.zones_tab = ZonesTab(services)
        self.schedule_tab = ScheduleTab(services)
        self.dashboard_tab = DashboardTab(services)
        self.settings_tab = SettingsTab(services)
        self.stations_tab.stationSelected.connect(self.presets_tab.set_active_station)
        self.tabs.addTab(self.devices_tab, "Geräte")
        self.tabs.addTab(self.presets_tab, "Presets")
        self.tabs.addTab(self.stations_tab, "Sender")
        self.tabs.addTab(self.zones_tab, "Zonen")
        self.tabs.addTab(self.schedule_tab, "Zeitplan")
        self.tabs.addTab(self.dashboard_tab, "Dashboard")
        self.tabs.addTab(self.settings_tab, "Einstellungen")
        self.tabs.currentChanged.connect(self.handle_tab_change)
        layout.addWidget(self.tabs)

    def handle_tab_change(self, _index: int) -> None:
        self.devices_tab.refresh_table()
        self.stations_tab.refresh_controls()
        self.presets_tab.refresh_devices()
