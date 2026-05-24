"""Volume slider widget."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSlider


class VolumeSlider(QSlider):
    def __init__(self) -> None:
        super().__init__(Qt.Orientation.Horizontal)
        self.setRange(0, 100)
        self.setValue(20)
