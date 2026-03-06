"""Register / unregister Vocalix to start on login."""

import sys
import os

_IS_WIN = sys.platform == "win32"
_IS_MAC = sys.platform == "darwin"

_APP_NAME = "Vocalix"


def _get_launch_command() -> str:
    if getattr(sys, "_MEIPASS", None):
        return f'"{sys.executable}"'
    script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "main.py")
    return f'"{sys.executable}" "{script}"'


def enable():
    """Register Vocalix to start on login."""
    if _IS_WIN:
        _win_set(True)
    elif _IS_MAC:
        _mac_set(True)


def disable():
    """Remove Vocalix from login startup."""
    if _IS_WIN:
        _win_set(False)
    elif _IS_MAC:
        _mac_set(False)


def is_enabled() -> bool:
    if _IS_WIN:
        return _win_is_enabled()
    elif _IS_MAC:
        return _mac_is_enabled()
    return False


# -- Windows: Registry ---------------------------------------------------------

def _win_set(on: bool):
    import winreg
    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        0, winreg.KEY_SET_VALUE,
    )
    try:
        if on:
            winreg.SetValueEx(key, _APP_NAME, 0, winreg.REG_SZ, _get_launch_command())
        else:
            try:
                winreg.DeleteValue(key, _APP_NAME)
            except FileNotFoundError:
                pass
    finally:
        winreg.CloseKey(key)


def _win_is_enabled() -> bool:
    import winreg
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_READ,
        )
        try:
            winreg.QueryValueEx(key, _APP_NAME)
            return True
        except FileNotFoundError:
            return False
        finally:
            winreg.CloseKey(key)
    except OSError:
        return False


# -- macOS: LaunchAgent --------------------------------------------------------

_PLIST_DIR = os.path.expanduser("~/Library/LaunchAgents")
_PLIST_PATH = os.path.join(_PLIST_DIR, "com.vocalix.app.plist")

_PLIST_TEMPLATE = """\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.vocalix.app</string>
    <key>ProgramArguments</key>
    <array>
{args}
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
"""


def _mac_set(on: bool):
    if on:
        if getattr(sys, "_MEIPASS", None):
            app_path = os.path.dirname(os.path.dirname(os.path.dirname(sys.executable)))
            args_xml = f"        <string>open</string>\n        <string>{app_path}</string>"
        else:
            script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "main.py")
            args_xml = f"        <string>{sys.executable}</string>\n        <string>{script}</string>"

        os.makedirs(_PLIST_DIR, exist_ok=True)
        with open(_PLIST_PATH, "w") as f:
            f.write(_PLIST_TEMPLATE.format(args=args_xml))
    else:
        try:
            os.remove(_PLIST_PATH)
        except FileNotFoundError:
            pass


def _mac_is_enabled() -> bool:
    return os.path.exists(_PLIST_PATH)
