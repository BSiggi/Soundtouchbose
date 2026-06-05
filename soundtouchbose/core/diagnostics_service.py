"""Diagnostics collection and export for support."""

from __future__ import annotations

import json
import platform
import socket
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile

from soundtouchbose import __version__
from soundtouchbose.core.error_texts import user_error_text


class DiagnosticsService:
    def __init__(self, services=None) -> None:
        self.services = services

    @staticmethod
    def _check_port(host: str, port: int, timeout: float = 1.0) -> bool:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except OSError:
            return False

    def _collect_local_addresses(self) -> list[str]:
        addresses = {entry[4][0] for entry in socket.getaddrinfo(socket.gethostname(), None) if entry[4]}
        return sorted(address for address in addresses if ":" not in address)

    def _tail_log(self, name: str = "app.log", max_lines: int = 250) -> str:
        path = self.services.config_store.logs_dir / name
        if not path.exists():
            return ""
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        return "\n".join(lines[-max_lines:])

    def collect_report(self) -> dict[str, Any]:
        settings = self.services.config_store.load_settings().copy()
        if "home_assistant_token" in settings:
            settings["home_assistant_token"] = "***masked***"
        devices = []
        network_checks = []
        bridge_mappings = self.services.preset_manager.load_bridge_mappings()
        bridge_mappings_summary = {
            ip_address: {
                preset_number: {
                    "identifier": str(station_payload.get("identifier", "")),
                    "name": str(station_payload.get("name", "")),
                    "source": str(station_payload.get("source", "")),
                    "location": str(station_payload.get("location", "")),
                }
                for preset_number, station_payload in sorted(slots.items(), key=lambda item: item[0])
            }
            for ip_address, slots in sorted(bridge_mappings.items(), key=lambda item: item[0])
        }
        for device in self.services.device_manager.all_devices():
            reachable_8090 = self._check_port(device.ip_address, 8090)
            network_checks.append(
                {
                    "ip_address": device.ip_address,
                    "port_8090_reachable": reachable_8090,
                }
            )
            devices.append(asdict(device))
        firewall_hints = []
        if any(not item["port_8090_reachable"] for item in network_checks):
            firewall_hints.append("Port 8090 ist auf mindestens einem Gerät nicht erreichbar. Firewall oder Netzsegment prüfen.")
        report = {
            "program": "SoundTouchBose",
            "version": settings.get("installed_version", __version__),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "os": {
                "platform": platform.platform(),
                "system": platform.system(),
                "release": platform.release(),
                "python": platform.python_version(),
            },
            "local_addresses": self._collect_local_addresses(),
            "settings": settings,
            "preset_bridge": {
                "enabled": bool(settings.get("preset_bridge_enabled", False)),
                "mapped_devices": len(bridge_mappings),
                "mapped_slots": sum(len(entry) for entry in bridge_mappings.values()),
                "configured_mappings": bridge_mappings_summary,
                "runtime": self.services.preset_bridge.diagnostics_snapshot(),
            },
            "devices": devices,
            "network_checks": network_checks,
            "firewall_hints": firewall_hints,
            "recent_errors": [line for line in self._tail_log().splitlines() if "ERROR" in line or "WARNING" in line][-50:],
        }
        return report

    def export(self, destination_zip: Path) -> Path:
        destination_zip.parent.mkdir(parents=True, exist_ok=True)
        report = self.collect_report()
        with ZipFile(destination_zip, "w", compression=ZIP_DEFLATED) as archive:
            archive.writestr("diagnostics/report.json", json.dumps(report, ensure_ascii=False, indent=2))
            archive.writestr("diagnostics/app.log.tail.txt", self._tail_log())
            update_log = self._tail_log("update.log")
            if update_log:
                archive.writestr("diagnostics/update.log.tail.txt", update_log)
        return destination_zip

    def safe_call_summary(self, operation: str, exc: Exception) -> str:
        return f"{operation} fehlgeschlagen: {user_error_text(exc)}"
