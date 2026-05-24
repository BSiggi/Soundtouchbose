"""Centralized user-facing error and status texts."""

from __future__ import annotations

from collections.abc import Mapping

from soundtouchbose.api.client import SoundTouchRequestError

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
    if isinstance(exc, SoundTouchRequestError):
        if exc.status_code is not None:
            return f"Gerät hat die Anfrage am Endpunkt {exc.endpoint} abgelehnt (HTTP {exc.status_code})."
        return "Verbindung zum Gerät fehlgeschlagen. Bitte Erreichbarkeit und Firewall prüfen."
    raw = str(exc).strip()
    lowered = raw.lower()
    if "invalid_source" in lowered:
        return "Keine gültige Quelle am Gerät verfügbar. Bitte Quelle oder Sender prüfen."
    if "service unavailable" in lowered or "dienst nicht verfügbar" in lowered:
        return "Gerätedienst ist aktuell nicht verfügbar. Bitte Gerät und Netzwerk prüfen."
    if "soundtouch request failed" in lowered or "connection" in lowered or "timeout" in lowered:
        return "Verbindung zum Gerät fehlgeschlagen. Bitte Erreichbarkeit und Firewall prüfen."
    if raw:
        return f"Aktion konnte nicht durchgeführt werden: {raw}"
    return "Aktion konnte nicht durchgeführt werden."
