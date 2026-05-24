from pathlib import Path

from soundtouchbose.core.config import ConfigStore, DEFAULT_SETTINGS


def test_settings_merge_defaults(tmp_path: Path) -> None:
    store = ConfigStore(tmp_path)
    store.save_settings({"web_ui_port": 9999})

    settings = store.load_settings()

    assert settings["web_ui_port"] == 9999
    assert settings["home_assistant_port"] == DEFAULT_SETTINGS["home_assistant_port"]


def test_backup_and_restore_json_files(tmp_path: Path) -> None:
    store = ConfigStore(tmp_path)
    store.save_json("devices.json", [{"ip_address": "1.2.3.4"}])
    store.save_json("stations.json", [{"identifier": "s1"}])
    backup = tmp_path / "backup.zip"

    store.backup_to_zip(backup)
    store.save_json("devices.json", [])
    store.restore_from_zip(backup)

    assert store.load_json("devices.json", []) == [{"ip_address": "1.2.3.4"}]
    assert store.load_json("stations.json", []) == [{"identifier": "s1"}]


def test_settings_generate_secure_home_assistant_token(tmp_path: Path) -> None:
    store = ConfigStore(tmp_path)

    settings = store.load_settings()

    assert settings["home_assistant_token"]
    assert settings["home_assistant_token"] != DEFAULT_SETTINGS["home_assistant_token"]
    assert store.load_json("settings.json", {})["home_assistant_token"] == settings["home_assistant_token"]
