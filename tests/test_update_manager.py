import json
from pathlib import Path
from zipfile import ZipFile

from soundtouchbose.core.config import ConfigStore
from soundtouchbose.core.update_manager import UpdateManager


def build_zip(path: Path, payload: dict[str, str]) -> Path:
    with ZipFile(path, "w") as archive:
        for name, content in payload.items():
            archive.writestr(name, content)
    return path


def test_apply_update_package_creates_backup_and_updates_files(tmp_path: Path) -> None:
    config_store = ConfigStore(tmp_path / "config")
    app_root = tmp_path / "app"
    app_root.mkdir(parents=True)
    target = app_root / "example.txt"
    target.write_text("old", encoding="utf-8")
    package = build_zip(
        tmp_path / "update.zip",
        {
            "manifest.json": json.dumps({"version": "0.2.0"}),
            "example.txt": "new",
        },
    )
    manager = UpdateManager(config_store, app_root, "0.1.0")

    result = manager.apply_update_package(package)

    assert result.package_version == "0.2.0"
    assert target.read_text(encoding="utf-8") == "new"
    assert result.backup_path.exists()
    assert config_store.load_settings()["installed_version"] == "0.2.0"


def test_apply_update_rejects_unsafe_paths(tmp_path: Path) -> None:
    config_store = ConfigStore(tmp_path / "config")
    app_root = tmp_path / "app"
    app_root.mkdir(parents=True)
    package = build_zip(tmp_path / "unsafe.zip", {"../evil.txt": "bad"})
    manager = UpdateManager(config_store, app_root, "0.1.0")

    try:
        manager.apply_update_package(package)
    except ValueError as exc:
        assert "Unsicherer Update-Pfad" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unsafe update path")
