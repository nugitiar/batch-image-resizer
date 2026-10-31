# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller specification file for macOS Apple Silicon (arm64).

Compiles Batch Image Resizer into a standalone .app bundle with Retina display
support, native Dark Mode, and bundled CustomTkinter assets.
"""

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules

project_dir = Path.cwd().resolve()

# Collect CustomTkinter assets (fonts, JSON color themes)
datas = collect_data_files("customtkinter")

# Collect TkinterDnD resources if installed
try:
    datas += collect_data_files("tkinterdnd2")
except Exception:
    pass

binaries = []
try:
    binaries += collect_dynamic_libs("tkinterdnd2")
except Exception:
    pass

hiddenimports = [
    "customtkinter",
    "PIL",
    "PIL.Image",
    "PIL.ImageTk",
    "tkinter",
    "tkinter.filedialog",
    "tkinter.messagebox",
    "src.core.config",
    "src.core.detector",
    "src.core.processor",
    "src.core.worker",
    "src.ui.app_window",
    "src.ui.components",
    "src.ui.dnd_handler",
]

# Add optional submodules
hiddenimports += collect_submodules("customtkinter")

block_cipher = None

a = Analysis(
    ["src/main.py"],
    pathex=[str(project_dir), str(project_dir / "src")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["matplotlib", "numpy", "scipy", "pytest", "IPython"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Batch Image Resizer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch="arm64",  # Explicitly target Apple Silicon M1/M2/M3/M4
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Batch Image Resizer",
)

app = BUNDLE(
    coll,
    name="Batch Image Resizer.app",
    icon=None,
    bundle_identifier="com.antigravity.batchresizer",
    info_plist={
        "CFBundleName": "Batch Image Resizer",
        "CFBundleDisplayName": "Batch Image Resizer",
        "CFBundleIdentifier": "com.antigravity.batchresizer",
        "CFBundleVersion": "1.0.0",
        "CFBundleShortVersionString": "1.0.0",
        "CFBundlePackageType": "APPL",
        "CFBundleSignature": "????",
        "LSMinimumSystemVersion": "11.0",
        "NSHighResolutionCapable": True,           # Enable Retina display rendering
        "NSRequiresAquaSystemAppearance": False,   # Enable macOS Dark/Light Mode switching
        "NSSupportsAutomaticGraphicsSwitching": True,
        "NSHumanReadableCopyright": "Copyright © 2026. All rights reserved.",
    },
)
