"""Configuration helpers for persistent local application data."""

from __future__ import annotations

import json
import os
import secrets
from pathlib import Path
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile

APP_NAME = "SoundTouchBose"
DEFAULT_SETTINGS = {
    "autostart": False,
    "minimize_to_tray": True,
    "web_ui_enabled": True,
    "web_ui_port": 8765,
    "home_assistant_enabled": False,
    "home_assistant_port": 8766,
    "home_assistant_token": "change-me",
    "night_mode_enabled": False,
    "night_mode_start": "22:00",
    "night_mode_end": "07:00",
    "night_mode_max_volume": 20,
    "preferred_device_ips": [],
}


class ConfigStore:
    """Read and write JSON config files in the app data directory."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or self.default_base_dir()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.backups_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def default_base_dir() -> Path:
        override = os.environ.get("SOUNDTOUCHBOSE_CONFIG_DIR")
        if override:
            return Path(override).expanduser().resolve()
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / APP_NAME
        return Path.home() / ".config" / APP_NAME

    @property
    def logs_dir(self) -> Path:
        return self.base_dir / "logs"

    @property
    def backups_dir(self) -> Path:
        return self.base_dir / "backups"

    def path_for(self, filename: str) -> Path:
        return self.base_dir / filename

    def load_json(self, filename: str, default: Any) -> Any:
        path = self.path_for(filename)
        if not path.exists():
            return default
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def save_json(self, filename: str, payload: Any) -> Path:
        path = self.path_for(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        return path

    def load_settings(self) -> dict[str, Any]:
        loaded = self.load_json("settings.json", {})
        settings = self._prepare_settings(loaded)
        if loaded.get("home_assistant_token") != settings["home_assistant_token"]:
            self.save_json("settings.json", settings)
        return settings

    def save_settings(self, settings: dict[str, Any]) -> Path:
        merged = self._prepare_settings(settings)
        return self.save_json("settings.json", merged)

    def _prepare_settings(self, settings: dict[str, Any]) -> dict[str, Any]:
        merged = DEFAULT_SETTINGS.copy()
        merged.update(settings)
        token = str(merged.get("home_assistant_token", "")).strip()
        if not token or token == DEFAULT_SETTINGS["home_assistant_token"]:
            merged["home_assistant_token"] = secrets.token_urlsafe(24)
        return merged

    def backup_to_zip(self, zip_path: Path) -> Path:
        zip_path.parent.mkdir(parents=True, exist_ok=True)
        with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as archive:
            for file_path in sorted(self.base_dir.glob("*.json")):
                archive.write(file_path, arcname=file_path.name)
        return zip_path

    def restore_from_zip(self, zip_path: Path) -> None:
        with ZipFile(zip_path, "r") as archive:
            archive.extractall(self.base_dir)
