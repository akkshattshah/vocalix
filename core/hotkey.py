import threading
import keyboard
from PyQt5.QtCore import QObject, pyqtSignal


class HotkeyListener(QObject):
    """Listens for a global hotkey and emits toggle signals.

    Press once  -> start_recording
    Press again -> stop_recording
    """

    start_recording = pyqtSignal()
    stop_recording = pyqtSignal()

    def __init__(self, hotkey: str = "alt"):
        super().__init__()
        self._hotkey = hotkey
        self._recording = False
        self._suppressed = False
        self._thread: threading.Thread | None = None

    def start(self):
        keyboard.on_press_key(self._hotkey, self._on_press, suppress=False)

    def stop(self):
        keyboard.unhook_all()
        self._recording = False

    def restart(self, new_key: str):
        """Swap the hotkey at runtime."""
        self.stop()
        self._hotkey = new_key
        self.start()

    def suppress(self, value: bool = True):
        self._suppressed = value

    def _on_press(self, _event):
        if self._suppressed:
            return
        if not self._recording:
            self._recording = True
            self.start_recording.emit()
        else:
            self._recording = False
            self.stop_recording.emit()
