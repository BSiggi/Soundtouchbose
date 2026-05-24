"""WebSocket client for receiving SoundTouch live updates."""

from __future__ import annotations

import logging
import threading
from typing import Callable

import websocket

LOGGER = logging.getLogger(__name__)


class SoundTouchWebSocketClient:
    """Background websocket connector using the gabbo subprotocol."""

    def __init__(self, ip_address: str, on_message: Callable[[str], None]) -> None:
        self.ip_address = ip_address
        self.on_message = on_message
        self._thread: threading.Thread | None = None
        self._app: websocket.WebSocketApp | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._app = websocket.WebSocketApp(
            f"ws://{self.ip_address}:8080/",
            subprotocols=["gabbo"],
            on_message=lambda _ws, payload: self.on_message(payload),
            on_error=lambda _ws, error: LOGGER.warning("WebSocket error for %s: %s", self.ip_address, error),
        )
        self._thread = threading.Thread(target=self._app.run_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._app:
            self._app.close()
