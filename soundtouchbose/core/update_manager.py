"""In-app update application with backup and rollback support."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from zipfile import ZIP_DEFLATED, ZipFile

from soundtouchbose.core.config import ConfigStore


@dataclass(slots=True)
class UpdateResult:
    backup_path: Path
    applied_files: list[str]
    package_version: str


class UpdateManager:
    def __init__(self, config_store: ConfigStore, app_root: Path, current_version: str) -> None:
        self.config_store = config_store
        self.app_root = app_root
        self.current_version = current_version

    def _timestamp(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")

    def _safe_members(self, package: ZipFile) -> list[str]:
        members: list[str] = []
        for member in package.namelist():
            normalized = PurePosixPath(member)
            if normalized.name == "":
                continue
            if normalized.is_absolute() or ".." in normalized.parts:
                raise ValueError(f"Unsicherer Update-Pfad: {member}")
            members.append(str(normalized))
        return members

    def _create_pre_update_backup(self) -> Path:
        backup_path = self.config_store.backups_dir / f"pre-update-{self._timestamp()}.zip"
        self.config_store.backup_to_zip(backup_path)
        return backup_path

    def _write_update_log(self, package_path: Path, package_version: str, applied_files: list[str]) -> None:
        log_path = self.config_store.logs_dir / "update.log"
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(f"[{datetime.now(timezone.utc).isoformat()}] package={package_path.name} version={package_version}\n")
            for entry in applied_files:
                handle.write(f"  - {entry}\n")

    def apply_update_package(self, package_path: Path) -> UpdateResult:
        if not package_path.exists():
            raise FileNotFoundError(package_path)
        pre_update_backup = self._create_pre_update_backup()
        applied_files: list[str] = []
        previous_content: dict[Path, bytes | None] = {}
        package_version = self.current_version
        with ZipFile(package_path, "r") as package:
            members = self._safe_members(package)
            if "manifest.json" in members:
                manifest = json.loads(package.read("manifest.json").decode("utf-8"))
                package_version = str(manifest.get("version", package_version))
            try:
                for member in members:
                    target = self.app_root / member
                    target.parent.mkdir(parents=True, exist_ok=True)
                    previous_content[target] = target.read_bytes() if target.exists() else None
                    target.write_bytes(package.read(member))
                    applied_files.append(member)
            except Exception:
                for target, old_content in previous_content.items():
                    if old_content is None:
                        target.unlink(missing_ok=True)
                    else:
                        target.write_bytes(old_content)
                raise
        self._write_update_log(package_path, package_version, applied_files)
        settings = self.config_store.load_settings()
        history = list(settings.get("update_history", []))
        history.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "package": package_path.name,
                "version": package_version,
                "backup": str(pre_update_backup),
            }
        )
        settings["update_history"] = history[-50:]
        settings["installed_version"] = package_version
        self.config_store.save_settings(settings)
        return UpdateResult(backup_path=pre_update_backup, applied_files=applied_files, package_version=package_version)

    def rollback_from_backup(self, backup_path: Path) -> None:
        with ZipFile(backup_path, "r", compression=ZIP_DEFLATED) as archive:
            archive.extractall(self.config_store.base_dir)
