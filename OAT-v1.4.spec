# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['D:/pycharm/pythonProject/OnmyojiProject/main.py'],
    pathex=[],
    binaries=[],
    datas=[('E:\\OAT\\_internal\\Onmyoji', 'Onmyoji')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='OAT-v1.4',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['E:\\Onmyoji\\Onmyoji\\icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='OAT-v1.4',
)
