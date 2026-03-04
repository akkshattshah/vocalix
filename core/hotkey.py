import sys
import threading
from PyQt5.QtCore import QObject, pyqtSignal

_IS_MAC = sys.platform == "darwin"

if _IS_MAC:
    from pynput import keyboard as pynput_kb
else:
    import keyboard

_PYNPUT_NAME_MAP = {
    "caps lock": "caps_lock",
    "page up": "page_up",
    "page down": "page_down",
    "print screen": "print_screen",
    "scroll lock": "scroll_lock",
    "num lock": "num_lock",
    "windows": "cmd",
}


class HotkeyListener(QObject):
    """Listens for a global hotkey and emits toggle signals.

    Press once  -> start_recording
    Press again -> stop_recording

    Uses `pynput` on macOS (needs Accessibility permission) and the
    `keyboard` library on Windows/Linux (no special permissions).
    """

    start_recording = pyqtSignal()
    stop_recording = pyqtSignal()

    def __init__(self, hotkey: str = "ctrl"):
        super().__init__()
        self._hotkey = hotkey
        self._recording = False
        self._suppressed = False
        self._listener = None

    def start(self):
        if _IS_MAC:
            self._start_pynput()
        else:
            keyboard.on_press_key(self._hotkey, self._on_press, suppress=False)

    def _start_pynput(self):
        self._listener = pynput_kb.Listener(on_press=self._on_pynput_press)
        self._listener.daemon = True
        self._listener.start()

    def _key_matches(self, key) -> bool:
        target = _PYNPUT_NAME_MAP.get(self._hotkey.lower(), self._hotkey.lower())

        if isinstance(key, pynput_kb.Key):
            name = key.name
            if name == target:
                return True
            if (name.endswith("_l") or name.endswith("_r")) and name[:-2] == target:
                return True
        elif isinstance(key, pynput_kb.KeyCode) and key.char:
            if key.char.lower() == target:
                return True

        return False

    def _on_pynput_press(self, key):
        if self._suppressed:
            return
        if self._key_matches(key):
            self._toggle()

    def stop(self):
        if _IS_MAC:
            if self._listener:
                self._listener.stop()
                self._listener = None
        else:
            keyboard.unhook_all()
        self._recording = False

    def restart(self, new_key: str):
        """Swap the hotkey at runtime."""
        self.stop()
        self._hotkey = new_key
        self.start()

    def suppress(self, value: bool = True):
        self._suppressed = value

    def _toggle(self):
        if not self._recording:
            self._recording = True
            self.start_recording.emit()
        else:
            self._recording = False
            self.stop_recording.emit()

    def _on_press(self, _event):
        if self._suppressed:
            return
        self._toggle()
