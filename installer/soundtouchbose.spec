# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_data_files

# SPECPATH is the directory containing this spec file (installer/).
# The project root is one level up.
project_root = os.path.abspath(os.path.join(SPECPATH, '..'))
sys.path.insert(0, project_root)

datas = collect_data_files('soundtouchbose')

block_cipher = None

a = Analysis(
    [os.path.join(project_root, 'soundtouchbose', '__main__.py')],
    pathex=[project_root],
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
    icon=os.path.join(project_root, 'soundtouchbose', 'resources', 'icon.ico'),
)
