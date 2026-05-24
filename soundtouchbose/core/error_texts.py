"""Centralized user-facing error and status texts."""

from __future__ import annotations

from datetime import datetime, timezone
from collections.abc import Mapping

SOURCE_TEXTS: dict[str, str] = {
    "invalid_source": "Keine gültige Quelle verfügbar",
    "standby": "Standby",
    "bluetooth": "Bluetooth",
    "aux": "AUX",
    "airplay": "AirPlay",
    "internet_radio": "Internetradio",
}


def source_display_text(raw_source: str, now_playing: Mapping[str, object] | None = None) -> str:
    source = (raw_source or "").strip()
    if not source:
        return "Keine Quelle erkannt"
    mapped = SOURCE_TEXTS.get(source.lower())
    if mapped:
        return mapped
    item_name = str((now_playing or {}).get("item_name") or (now_playing or {}).get("station_name") or "").strip()
    if item_name:
        return item_name
    return source.replace("_", " ").strip().title()


def is_valid_source(raw_source: str) -> bool:
    source = (raw_source or "").strip().lower()
    return bool(source) and source not in {"invalid_source", "none", "unknown"}


def user_error_text(exc: Exception) -> str:
    metadata = error_details(exc)
    category = metadata.get("category")
    status_code = metadata.get("http_status")
    operation = str(metadata.get("operation") or "")
    raw = str(exc).strip()
    lowered = raw.lower()
    if category == "invalid_source" or "invalid_source" in lowered:
        return "Gerät ist erreichbar, aber die Quelle ist derzeit nicht lesbar (INVALID_SOURCE)."
    if category == "http_status":
        operation_hint = "Preset/Quellvorgang" if operation in {"select", "preset_write", "key"} else "Gerätevorgang"
        if status_code is not None:
            return f"Gerät ist erreichbar, aber Bose hat den {operation_hint} mit HTTP {status_code} abgelehnt oder mit Fehler beantwortet."
        return f"Gerät ist erreichbar, aber Bose hat den {operation_hint} abgelehnt oder mit Fehler beantwortet."
    if category in {"network", "timeout"} or "soundtouch request failed" in lowered or "connection" in lowered or "timeout" in lowered:
        return "Verbindung zum Gerät fehlgeschlagen. Bitte IP-Adresse, Erreichbarkeit und ggf. Firewall prüfen."
    if "service unavailable" in lowered or "dienst nicht verfügbar" in lowered:
        return "Gerätedienst ist aktuell nicht verfügbar. Bitte Gerät und Netzwerk prüfen."
    if raw:
        return f"Aktion konnte nicht durchgeführt werden: {raw}"
    return "Aktion konnte nicht durchgeführt werden."


def error_details(exc: Exception, operation: str | None = None) -> dict[str, object]:
    status_code = getattr(exc, "status_code", None)
    endpoint = str(getattr(exc, "endpoint", "") or "")
    op_name = operation or str(getattr(exc, "operation", "") or "")
    category = str(getattr(exc, "kind", "") or "")
    raw = str(exc).strip()
    lowered = raw.lower()
    if not category:
        if "invalid_source" in lowered:
            category = "invalid_source"
        elif "timeout" in lowered:
            category = "timeout"
        elif "connection" in lowered or "soundtouch request failed" in lowered:
            category = "network"
        elif "http " in lowered:
            category = "http_status"
        else:
            category = "unknown"
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "operation": op_name or None,
        "endpoint": endpoint or None,
        "http_status": int(status_code) if isinstance(status_code, int) else None,
        "category": category,
        "message": raw or "Unbekannter Fehler",
    }
