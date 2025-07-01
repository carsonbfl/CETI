# -*- mode: python ; coding: utf-8 -*-
import sys
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

a = Analysis(
    ['CETI.py'],
    pathex=['.'],  # adjust if your script is in a subfolder
    binaries=[],
    datas=[
        ('assets/CETI_logo-export.ico', 'assets'),  # correct icon path
    ],
    hiddenimports=collect_submodules('gui') + collect_submodules('core') + ['PyQt5.sip'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,  
    a.zipfiles,
    a.datas,
    [],
    name='CETI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='assets/CETI_logo-export.ico'
)


coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='CETI'
)
