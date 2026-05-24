"""Live dashboard tab."""

from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QScrollArea, QVBoxLayout, QWidget

from soundtouchbose.api.websocket_client import SoundTouchWebSocketClient
from soundtouchbose.core.error_texts import source_display_text
from soundtouchbose.services import Services
from soundtouchbose.gui.widgets.device_card import DeviceCard


class DashboardTab(QWidget):
    def __init__(self, services: Services) -> None:
        super().__init__()
        self.services = services
        self.cards: dict[str, DeviceCard] = {}
        self.websocket_clients: dict[str, SoundTouchWebSocketClient] = {}
        layout = QVBoxLayout(self)
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.container)
        layout.addWidget(scroll)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_cards)
        self.timer.start(10_000)
        self.refresh_cards()

    def refresh_cards(self) -> None:
        existing = set(self.cards)
        for device in self.services.device_manager.all_devices():
            card = self.cards.get(device.ip_address)
            if card is None:
                card = DeviceCard(device.ip_address, device.name)
                card.volumeChanged.connect(self.set_volume)
                card.controlPressed.connect(self.send_key)
                self.cards[device.ip_address] = card
                self.container_layout.addWidget(card)
            try:
                snapshot = self.services.client_factory(device.ip_address).get_now_playing()
                card.update_state(online=True, source=source_display_text(str(snapshot.get("source", "")), snapshot))
                if device.ip_address not in self.websocket_clients:
                    self.websocket_clients[device.ip_address] = SoundTouchWebSocketClient(device.ip_address, lambda _msg, ip=device.ip_address: self.refresh_single(ip))
                    self.websocket_clients[device.ip_address].start()
            except Exception:
                card.update_state(online=False, source="")
            existing.discard(device.ip_address)
        for ip_address in existing:
            card = self.cards.pop(ip_address)
            card.deleteLater()

    def refresh_single(self, ip_address: str) -> None:
        card = self.cards.get(ip_address)
        if not card:
            return
        try:
            snapshot = self.services.client_factory(ip_address).get_now_playing()
            card.update_state(online=True, source=source_display_text(str(snapshot.get("source", "")), snapshot))
        except Exception:
            card.update_state(online=False, source="")

    def set_volume(self, ip_address: str, value: int) -> None:
        self.services.client_factory(ip_address).set_volume(value)

    def send_key(self, ip_address: str, key_name: str) -> None:
        client = self.services.client_factory(ip_address)
        client.send_key(key_name, "press")
        client.send_key(key_name, "release")
