"""Optional cleanup helpers for uninstall and maintenance."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from soundtouchbose.core.config import ConfigStore
from soundtouchbose.runtime import sync_autostart


class CleanupService:
    def __init__(self, config_store: ConfigStore) -> None:
        self.config_store = config_store

    def cleanup_old_backups(self, keep_latest: int = 5) -> list[str]:
        backups = sorted(self.config_store.backups_dir.glob("*.zip"), key=lambda path: path.stat().st_mtime, reverse=True)
        removed: list[str] = []
        for path in backups[keep_latest:]:
            path.unlink(missing_ok=True)
            removed.append(path.name)
        return removed

    def stop_windows_services(self, service_names: list[str]) -> dict[str, str]:
        statuses: dict[str, str] = {}
        if not sys.platform.startswith("win"):
            return statuses
        for name in service_names:
            query = subprocess.run(["sc", "query", name], capture_output=True, text=True, check=False)
            if query.returncode != 0:
                statuses[name] = "nicht installiert"
                continue
            stop = subprocess.run(["sc", "stop", name], capture_output=True, text=True, check=False)
            statuses[name] = "gestoppt" if stop.returncode == 0 else "stop fehlgeschlagen"
        return statuses

    def run_cleanup(self, *, remove_autostart: bool = True, keep_backups: int = 5) -> dict[str, object]:
        if remove_autostart:
            sync_autostart(False)
        removed_backups = self.cleanup_old_backups(keep_latest=keep_backups)
        service_status = self.stop_windows_services(["SoundTouchBoseService", "soundtouchbose"])
        return {
            "autostart_removed": remove_autostart,
            "removed_backups": removed_backups,
            "service_status": service_status,
            "config_directory": str(Path(self.config_store.base_dir)),
        }
