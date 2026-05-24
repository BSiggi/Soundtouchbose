# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import sys

from PyInstaller.utils.hooks import collect_data_files

PROJECT_ROOT = Path(SPECPATH).resolve().parent
ENTRYPOINT = PROJECT_ROOT / "soundtouchbose" / "__main__.py"
ICON_PATH = PROJECT_ROOT / "soundtouchbose" / "resources" / "icon.ico"
# collect_data_files() runs while evaluating this spec, before Analysis.pathex is applied.
added_project_root = False
if not sys.path or sys.path[0] != str(PROJECT_ROOT):
    sys.path.insert(0, str(PROJECT_ROOT))
    added_project_root = True
if not ENTRYPOINT.exists():
    raise FileNotFoundError(f"PyInstaller entrypoint not found: {ENTRYPOINT}")
if not ICON_PATH.exists():
    raise FileNotFoundError(f"PyInstaller icon not found: {ICON_PATH}")

try:
    datas = collect_data_files('soundtouchbose')
finally:
    if added_project_root and sys.path and sys.path[0] == str(PROJECT_ROOT):
        del sys.path[0]

block_cipher = None

a = Analysis(
    [str(ENTRYPOINT)],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SoundTouchBose',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon=str(ICON_PATH),
)
