"""HTTP client for the local Bose SoundTouch API."""

from __future__ import annotations

import logging
import time
from typing import Any, Callable
from urllib.parse import urlparse

import requests
from requests import Response, Session

from soundtouchbose.api.xml_helpers import (
    build_content_item_xml,
    build_key_xml,
    build_volume_xml,
    build_zone_xml,
    parse_info_xml,
    parse_now_playing_xml,
    parse_presets_xml,
    parse_sources_xml,
)
from soundtouchbose.core.station_library import Station

LOGGER = logging.getLogger(__name__)


class SoundTouchRequestError(RuntimeError):
    """Raised when a SoundTouch endpoint request fails."""

    def __init__(self, url: str, *, status_code: int | None = None, details: str = "") -> None:
        self.url = url
        self.status_code = status_code
        self.details = details.strip()
        path = urlparse(url).path or "/"
        if status_code is not None:
            message = f"SoundTouch request failed for {url} (HTTP {status_code})"
        else:
            message = f"SoundTouch request failed for {url}"
        if self.details:
            message = f"{message}: {self.details}"
        self.endpoint = path
        super().__init__(message)


class SoundTouchClient:
    """Small retrying wrapper around the SoundTouch HTTP/XML endpoints."""

    def __init__(self, ip_address: str, *, timeout: int = 5, retries: int = 3, session: Session | None = None) -> None:
        self.ip_address = ip_address
        self.timeout = timeout
        self.retries = retries
        self.session = session or requests.Session()
        self.base_url = f"http://{ip_address}:8090"

    def _request(self, method: str, path: str, *, data: str | None = None) -> Response:
        last_error: SoundTouchRequestError | None = None
        url = f"{self.base_url}{path}"
        headers = {"Content-Type": "application/xml; charset=utf-8"} if data is not None else None
        for attempt in range(1, self.retries + 1):
            try:
                response = self.session.request(method, url, data=data, headers=headers, timeout=self.timeout)
                response.raise_for_status()
                return response
            except requests.RequestException as exc:  # pragma: no cover - thin wrapper
                status_code = None
                if exc.response is not None:
                    status_code = exc.response.status_code
                last_error = SoundTouchRequestError(url, status_code=status_code, details=str(exc))
                LOGGER.warning("Request to %s failed (%s/%s): %s", url, attempt, self.retries, exc)
                if attempt < self.retries:
                    time.sleep(0.5 * attempt)
        raise last_error or SoundTouchRequestError(url)

    def get_info(self) -> dict[str, Any]:
        return parse_info_xml(self._request("GET", "/info").text)

    def get_now_playing(self) -> dict[str, Any]:
        return parse_now_playing_xml(self._request("GET", "/now_playing").text)

    def get_presets(self) -> list[dict[str, Any]]:
        return parse_presets_xml(self._request("GET", "/presets").text)

    def get_sources(self) -> list[dict[str, Any]]:
        return parse_sources_xml(self._request("GET", "/sources").text)

    def validate(self) -> bool:
        info = self.get_info()
        return bool(info.get("name"))

    def select(self, station: Station) -> None:
        self._request("POST", "/select", data=build_content_item_xml(station))

    def send_key(self, key_name: str, state: str) -> None:
        self._request("POST", "/key", data=build_key_xml(key_name, state))

    def set_volume(self, value: int) -> None:
        self._request("POST", "/volume", data=build_volume_xml(value))

    def power(self, state: str) -> None:
        if state.lower() not in {"on", "off"}:
            raise ValueError("Power state must be 'on' or 'off'")
        self.send_key("POWER", "press")
        self.send_key("POWER", "release")

    def set_zone(self, master_ip: str, member_ips: list[str]) -> None:
        self._request("POST", "/setZone", data=build_zone_xml(master_ip, member_ips))

    def get_zone(self) -> str:
        return self._request("GET", "/getZone").text

    def remove_zone(self, master_ip: str) -> None:
        self._request("POST", "/removeZone", data=f'<zone master="{master_ip}" />')

    def set_preset(
        self,
        preset_number: int,
        station: Station,
        *,
        wait_fn: Callable[[float], None] = time.sleep,
    ) -> bool:
        self.select(station)
        for _ in range(3):
            wait_fn(0.5)
            now_playing = self.get_now_playing()
            current_name = now_playing.get("item_name") or now_playing.get("station_name")
            if current_name == station.name:
                break
        key_name = f"PRESET_{preset_number}"
        self.send_key(key_name, "press")
        self.send_key(key_name, "release")
        presets = self.get_presets()
        return any(
            preset["id"] == preset_number and preset.get("location") == station.location
            for preset in presets
        )
