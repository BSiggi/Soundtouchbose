from pathlib import Path


def test_pyinstaller_spec_uses_project_root_for_entry_script() -> None:
    spec_path = Path(__file__).resolve().parents[1] / "installer" / "soundtouchbose.spec"
    spec_content = spec_path.read_text(encoding="utf-8")

    assert "PROJECT_ROOT = Path(SPECPATH).resolve().parent" in spec_content
    assert "sys.path.insert(0, str(PROJECT_ROOT))" in spec_content
    assert "str(PROJECT_ROOT / 'soundtouchbose' / '__main__.py')" in spec_content
