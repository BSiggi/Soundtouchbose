"""Large drag-and-drop preset button widget."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QPushButton


class PresetButton(QPushButton):
    stationDropped = Signal(int, str)

    def __init__(self, preset_number: int) -> None:
        super().__init__(f"Preset {preset_number}\nNicht belegt")
        self.preset_number = preset_number
        self.setAcceptDrops(True)
        self.setMinimumHeight(120)

    def dragEnterEvent(self, event) -> None:  # noqa: N802
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:  # noqa: N802
        self.stationDropped.emit(self.preset_number, event.mimeData().text())
        event.acceptProposedAction()
