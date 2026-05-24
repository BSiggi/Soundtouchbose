"""Helpers for building and parsing SoundTouch XML payloads."""

from __future__ import annotations

from html import escape
from typing import Any
from xml.etree import ElementTree as ET

from soundtouchbose.core.station_library import Station


def _try_parse_int(value: object) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def build_content_item_xml(station: Station) -> str:
    """Create a SoundTouch select payload from a station entry."""
    return (
        f'<ContentItem source="{escape(station.source)}" '
        f'type="{escape(station.item_type)}" '
        f'location="{escape(station.location)}" '
        f'sourceAccount="{escape(station.source_account)}" '
        f'isPresetable="{"true" if station.is_presetable else "false"}">'
        f"<itemName>{escape(station.name)}</itemName>"
        "</ContentItem>"
    )


def build_key_xml(key_name: str, state: str) -> str:
    return f'<key state="{escape(state)}" sender="Gabbo">{escape(key_name)}</key>'


def build_volume_xml(value: int) -> str:
    return f"<volume>{max(0, min(100, value))}</volume>"


def build_zone_xml(master_id: str, members: list[str]) -> str:
    members_xml = "".join(f'<member ipaddress="{escape(member)}" />' for member in members)
    return f'<zone master="{escape(master_id)}">{members_xml}</zone>'


def parse_info_xml(xml_text: str) -> dict[str, Any]:
    root = ET.fromstring(xml_text)
    return {
        "name": root.findtext("name", default=""),
        "device_id": root.findtext("deviceID", default=""),
        "type": root.findtext("type", default=""),
        "network_type": root.findtext("networkType", default=""),
        "software_version": root.findtext("softwareVersion", default=""),
        "mac_address": root.findtext("macAddress", default=""),
    }


def parse_now_playing_xml(xml_text: str) -> dict[str, Any]:
    root = ET.fromstring(xml_text)
    content = root.find("ContentItem")
    preset_id = _try_parse_int(root.attrib.get("presetID"))
    if preset_id is None and content is not None:
        preset_id = _try_parse_int(content.attrib.get("presetID"))
    return {
        "source": root.attrib.get("source", ""),
        "preset_id": preset_id,
        "device_name": root.findtext("deviceName", default=""),
        "item_name": root.findtext("itemName", default=""),
        "station_name": root.findtext("stationName", default=""),
        "track": root.findtext("track", default=""),
        "artist": root.findtext("artist", default=""),
        "album": root.findtext("album", default=""),
        "content_item": content.attrib if content is not None else {},
    }


def parse_presets_xml(xml_text: str) -> list[dict[str, Any]]:
    root = ET.fromstring(xml_text)
    presets: list[dict[str, Any]] = []
    for preset in root.findall("preset"):
        content = preset.find("ContentItem")
        presets.append(
            {
                "id": int(preset.attrib.get("id", "0")),
                "name": preset.findtext("ContentItem/itemName", default=""),
                "source": content.attrib.get("source", "") if content is not None else "",
                "location": content.attrib.get("location", "") if content is not None else "",
            }
        )
    return presets


def parse_sources_xml(xml_text: str) -> list[dict[str, Any]]:
    root = ET.fromstring(xml_text)
    return [source.attrib for source in root.findall("sourceItem")]
