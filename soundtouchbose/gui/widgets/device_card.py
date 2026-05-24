"""Dashboard card showing a device summary and controls."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from soundtouchbose.gui.widgets.volume_slider import VolumeSlider


class DeviceCard(QFrame):
    volumeChanged = Signal(str, int)
    controlPressed = Signal(str, str)

    def __init__(self, device_ip: str, device_name: str) -> None:
        super().__init__()
        self.device_ip = device_ip
        self.setProperty("card", True)
        layout = QVBoxLayout(self)
        self.title_label = QLabel(device_name)
        self.status_label = QLabel("Offline")
        self.source_label = QLabel("Keine Quelle")
        self.volume_slider = VolumeSlider()
        self.volume_slider.valueChanged.connect(lambda value: self.volumeChanged.emit(self.device_ip, value))
        controls = QHBoxLayout()
        for label, key in (("⏮", "PREV_TRACK"), ("⏯", "PLAY_PAUSE"), ("⏭", "NEXT_TRACK")):
            button = QPushButton(label)
            button.clicked.connect(lambda _checked=False, pressed=key: self.controlPressed.emit(self.device_ip, pressed))
            controls.addWidget(button)
        layout.addWidget(self.title_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.source_label)
        layout.addWidget(self.volume_slider)
        layout.addLayout(controls)

    def update_state(self, *, online: bool, source: str, volume: int = 20) -> None:
        self.status_label.setText("Online" if online else "Offline")
        self.source_label.setText(source or "Keine Quelle")
        self.volume_slider.blockSignals(True)
        self.volume_slider.setValue(volume)
        self.volume_slider.blockSignals(False)
