"""HTTP client for the local Bose SoundTouch API."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta
from typing import Any, Callable

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
    """Request error with operation metadata for UI and diagnostics.

    Attributes:
        ip_address: Target device IP.
        endpoint: HTTP endpoint path (for example ``/now_playing``).
        operation: Logical operation name used in UI/diagnostics (for example ``preset_write``).
        kind: Error category (``network``, ``timeout``, ``http_status``).
        status_code: HTTP status code if available.
    """

    def __init__(
        self,
        message: str,
        *,
        ip_address: str,
        endpoint: str,
        operation: str,
        kind: str,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.ip_address = ip_address
        self.endpoint = endpoint
        self.operation = operation
        self.kind = kind
        self.status_code = status_code


class SoundTouchClient:
    """Small retrying wrapper around the SoundTouch HTTP/XML endpoints."""

    def __init__(self, ip_address: str, *, timeout: int = 5, retries: int = 3, session: Session | None = None) -> None:
        self.ip_address = ip_address
        self.timeout = timeout
        self.retries = retries
        self.session = session or requests.Session()
        self.base_url = f"http://{ip_address}:8090"
        self._last_failure_logs: dict[str, datetime] = {}

    def _log_failure_once(self, key: str, message: str) -> None:
        now = datetime.now()
        threshold = now - timedelta(seconds=30)
        last = self._last_failure_logs.get(key)
        if last and last > threshold:
            return
        self._last_failure_logs[key] = now
        LOGGER.warning("%s", message)

    def _request(self, method: str, path: str, *, data: str | None = None, operation: str | None = None) -> Response:
        last_error: Exception | None = None
        url = f"{self.base_url}{path}"
        op_name = operation or path.lstrip("/") or "request"
        headers = {"Content-Type": "application/xml; charset=utf-8"} if data is not None else None
        for attempt in range(1, self.retries + 1):
            try:
                response = self.session.request(method, url, data=data, headers=headers, timeout=self.timeout)
                # SoundTouch devices in the field return UTF-8 XML but frequently omit
                # charset or report latin-1. Forcing UTF-8 avoids mojibake in names like
                # "BÜRO" and matches real device payload bytes.
                if not response.encoding or response.encoding.lower() in {"iso-8859-1", "latin-1"}:
                    response.encoding = "utf-8"
                response.raise_for_status()
                return response
            except requests.HTTPError as exc:  # pragma: no cover - thin wrapper
                last_error = exc
                status_code = exc.response.status_code if exc.response is not None else None
                key = f"{self.ip_address}:{path}:http:{status_code}"
                self._log_failure_once(
                    key,
                    f"Request to {url} failed ({attempt}/{self.retries}) with HTTP {status_code}: {exc}",
                )
                if attempt < self.retries:
                    time.sleep(0.5 * attempt)
            except requests.RequestException as exc:  # pragma: no cover - thin wrapper
                last_error = exc
                kind = "timeout" if isinstance(exc, requests.Timeout) else "network"
                key = f"{self.ip_address}:{path}:{kind}"
                self._log_failure_once(
                    key,
                    f"Request to {url} failed ({attempt}/{self.retries}) [{kind}]: {exc}",
                )
                if attempt < self.retries:
                    time.sleep(0.5 * attempt)
        if isinstance(last_error, requests.HTTPError):
            status_code = last_error.response.status_code if last_error.response is not None else None
            raise SoundTouchRequestError(
                f"SoundTouch HTTP {status_code} for {url}",
                ip_address=self.ip_address,
                endpoint=path,
                operation=op_name,
                kind="http_status",
                status_code=status_code,
            ) from last_error
        kind = "timeout" if isinstance(last_error, requests.Timeout) else "network"
        raise SoundTouchRequestError(
            f"SoundTouch request failed for {url}",
            ip_address=self.ip_address,
            endpoint=path,
            operation=op_name,
            kind=kind,
            status_code=None,
        ) from last_error

    def get_info(self) -> dict[str, Any]:
        return parse_info_xml(self._request("GET", "/info", operation="info").text)

    def get_now_playing(self) -> dict[str, Any]:
        return parse_now_playing_xml(self._request("GET", "/now_playing", operation="now_playing").text)

    def get_presets(self) -> list[dict[str, Any]]:
        return parse_presets_xml(self._request("GET", "/presets", operation="presets").text)

    def get_sources(self) -> list[dict[str, Any]]:
        return parse_sources_xml(self._request("GET", "/sources", operation="sources").text)

    def validate(self) -> bool:
        info = self.get_info()
        return bool(info.get("name"))

    def select(self, station: Station) -> None:
        self._request("POST", "/select", data=build_content_item_xml(station), operation="select")

    def send_key(self, key_name: str, state: str) -> None:
        self._request("POST", "/key", data=build_key_xml(key_name, state), operation="key")

    def set_volume(self, value: int) -> None:
        self._request("POST", "/volume", data=build_volume_xml(value), operation="volume")

    def power(self, state: str) -> None:
        if state.lower() not in {"on", "off"}:
            raise ValueError("Power state must be 'on' or 'off'")
        self.send_key("POWER", "press")
        self.send_key("POWER", "release")

    def set_zone(self, master_ip: str, member_ips: list[str]) -> None:
        self._request("POST", "/setZone", data=build_zone_xml(master_ip, member_ips), operation="set_zone")

    def get_zone(self) -> str:
        return self._request("GET", "/getZone", operation="get_zone").text

    def remove_zone(self, master_ip: str) -> None:
        self._request("POST", "/removeZone", data=f'<zone master="{master_ip}" />', operation="remove_zone")

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
