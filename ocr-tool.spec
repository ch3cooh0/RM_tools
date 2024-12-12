# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# tkinterdnd2のパスを取得
import tkinterdnd2
tkdnd_path = os.path.join(os.path.dirname(tkinterdnd2.__file__), 'tkdnd')

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        (tkdnd_path, 'tkinterdnd2/tkdnd'),  # tkdndライブラリを含める
    ],
    hiddenimports=['tkinterdnd2'],  # tkinterdnd2を明示的にインポート
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
    name='ocr-tool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version.txt',
    icon='icon.webp'
) 
