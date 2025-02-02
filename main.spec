# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('Algofox.py', '.'),
        ('Example.py', '.'),
        ('Exception.py', '.'),
        ('InteractiveSocketClient.py', '.'),
        ('InteractiveSocketExample.py', '.'),
        ('MainSettings.csv', '.'),
        ('MarketDataSocketClient.py', '.'),
        ('MarketdataSocketExample.py', '.'),
        ('OrderLogs.txt', '.'),
        ('README.md', '.'),
        ('requirements.txt', '.'),
        ('TradeSettings.csv', '.'),
        ('.gitignore', '.'),
        ('__init__.py', '.'),
        ('__version__.py', '.'),
        ('Apicon.py', '.'),
        ('config.ini', '.'),
        ('Connect.py', '.'),
        ('templates', 'templates')  # Add this line
    ],
    hiddenimports=['Algofox', 'requests', 'flask_wtf'],
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
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
