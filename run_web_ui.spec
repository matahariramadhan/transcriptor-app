# -*- mode: python ; coding: utf-8 -*-


import os

# Get the directory containing this spec file
SPEC_DIR = os.path.dirname(os.path.abspath(SPEC))
TEMPLATES_DIR = os.path.join(SPEC_DIR, 'interfaces', 'web', 'templates')
STATIC_DIR = os.path.join(SPEC_DIR, 'interfaces', 'web', 'static')

a = Analysis(
    ['run_web_ui.py'],
    pathex=[],
    binaries=[],
    # Add data files: (source_path, destination_in_bundle)
    datas=[
        (TEMPLATES_DIR, 'interfaces/web/templates'),
        (STATIC_DIR, 'interfaces/web/static'),
        (os.path.join(SPEC_DIR, '.env'), '.') # Add .env file to bundle root
    ],
    hiddenimports=[], # Might need to add hidden imports later if issues arise
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
    name='run_web_ui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='run_web_ui',
)
