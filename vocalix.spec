# -*- mode: python ; coding: utf-8 -*-
import os, sys

block_cipher = None
ROOT = os.path.abspath(".")

a = Analysis(
    ["main.py"],
    pathex=[ROOT],
    binaries=[],
    datas=[
        (os.path.join("auth", "templates", "login.html"), os.path.join("auth", "templates")),
        ("logo.png", "."),
    ],
    hiddenimports=[
        "engineio.async_drivers.threading",
        "scipy._lib.messagestream",
        "scipy.io",
        "scipy.io.wavfile",
        "pynput.keyboard._darwin",
        "pynput._util.darwin",
        "AppKit",
        "Foundation",
    ],
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
    [],
    exclude_binaries=True,
    name="Vocalix",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # windowed — no terminal
    icon=None,              # swap for vocalix.ico when available
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Vocalix",
)

# macOS only — ignored on Windows
app = BUNDLE(
    coll,
    name="Vocalix.app",
    icon=None,
    bundle_identifier="com.vocalix.app",
    info_plist={
        "LSUIElement": True,
        "NSMicrophoneUsageDescription": "Vocalix needs microphone access to transcribe your speech.",
        "NSAppleEventsUsageDescription": "Vocalix uses Accessibility to type text into other apps.",
    },
)
