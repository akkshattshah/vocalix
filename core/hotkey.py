import sys
import threading
from PyQt5.QtCore import QObject, pyqtSignal

_IS_MAC = sys.platform == "darwin"

if _IS_MAC:
    import Quartz
    from ApplicationServices import AXIsProcessTrustedWithOptions
    from CoreFoundation import kCFBooleanTrue
else:
    import keyboard

# ---------------------------------------------------------------------------
# macOS virtual key-code table (avoids TSM character mapping entirely)
# ---------------------------------------------------------------------------
_MAC_VK = {
    "ctrl":   (0x3B, 0x3E),
    "shift":  (0x38, 0x3C),
    "alt":    (0x3A, 0x3D),
    "cmd":    (0x37, 0x36),
    "caps lock": (0x39,),
    "space":  (0x31,),
    "return": (0x24,),  "enter": (0x24,),
    "tab":    (0x30,),
    "escape": (0x35,),  "esc":   (0x35,),
    "delete": (0x33,),  "backspace": (0x33,),
    "f1": (0x7A,), "f2": (0x78,), "f3": (0x63,), "f4": (0x76,),
    "f5": (0x60,), "f6": (0x61,), "f7": (0x62,), "f8": (0x64,),
    "f9": (0x65,), "f10": (0x6D,), "f11": (0x67,), "f12": (0x6F,),
    "up": (0x7E,), "down": (0x7D,), "left": (0x7B,), "right": (0x7C,),
    "home": (0x73,), "end": (0x77,),
    "page up": (0x74,), "page down": (0x79,),
    "a": (0x00,), "b": (0x0B,), "c": (0x08,), "d": (0x02,),
    "e": (0x0E,), "f": (0x03,), "g": (0x05,), "h": (0x04,),
    "i": (0x22,), "j": (0x26,), "k": (0x28,), "l": (0x25,),
    "m": (0x2E,), "n": (0x2D,), "o": (0x1F,), "p": (0x23,),
    "q": (0x0C,), "r": (0x0F,), "s": (0x01,), "t": (0x11,),
    "u": (0x20,), "v": (0x09,), "w": (0x0D,), "x": (0x07,),
    "y": (0x10,), "z": (0x06,),
    "0": (0x1D,), "1": (0x12,), "2": (0x13,), "3": (0x14,),
    "4": (0x15,), "5": (0x17,), "6": (0x16,), "7": (0x1A,),
    "8": (0x1C,), "9": (0x19,),
}

_MODIFIER_KEYS = {"ctrl", "shift", "alt", "cmd", "caps lock"}

_MODIFIER_FLAG = {
    "ctrl":      Quartz.kCGEventFlagMaskControl    if _IS_MAC else 0,
    "shift":     Quartz.kCGEventFlagMaskShift      if _IS_MAC else 0,
    "alt":       Quartz.kCGEventFlagMaskAlternate   if _IS_MAC else 0,
    "cmd":       Quartz.kCGEventFlagMaskCommand     if _IS_MAC else 0,
    "caps lock": Quartz.kCGEventFlagMaskAlphaShift  if _IS_MAC else 0,
}


class HotkeyListener(QObject):
    """Listens for a global hotkey and emits toggle signals.

    Press once  -> start_recording
    Press again -> stop_recording

    Uses a Quartz CGEvent tap on macOS (needs Accessibility permission) and
    the `keyboard` library on Windows/Linux.
    """

    start_recording = pyqtSignal()
    stop_recording = pyqtSignal()
    permission_needed = pyqtSignal()

    def __init__(self, hotkey: str = "ctrl"):
        super().__init__()
        self._hotkey = hotkey
        self._recording = False
        self._suppressed = False
        self._key_held = False
        self._tap = None
        self._run_loop_ref = None
        self._thread = None
        self._watchdog = None

    # -- public API --------------------------------------------------------

    def start(self):
        if _IS_MAC:
            self._start_quartz()
        else:
            keyboard.on_press_key(self._hotkey, self._on_press, suppress=False)

    def stop(self):
        if _IS_MAC:
            if self._watchdog is not None:
                self._watchdog.cancel()
                self._watchdog = None
            if self._tap is not None:
                Quartz.CGEventTapEnable(self._tap, False)
            if self._run_loop_ref is not None:
                Quartz.CFRunLoopStop(self._run_loop_ref)
            self._tap = None
            self._run_loop_ref = None
            self._thread = None
        else:
            keyboard.unhook_all()
        self._recording = False
        self._key_held = False

    def restart(self, new_key: str):
        self._suppressed = True
        self.stop()
        self._hotkey = new_key
        self.start()
        self._suppressed = False

    def suppress(self, value: bool = True):
        self._suppressed = value

    # -- macOS Quartz implementation ---------------------------------------

    def _start_quartz(self):
        self._key_held = False

        trusted = AXIsProcessTrustedWithOptions(
            {"AXTrustedCheckOptionPrompt": kCFBooleanTrue}
        )
        if not trusted:
            print(
                "[vocalix] Accessibility permission not granted. "
                "macOS should have shown a prompt.",
                flush=True,
            )
            self.permission_needed.emit()
            return

        mask = (
            Quartz.CGEventMaskBit(Quartz.kCGEventKeyDown)
            | Quartz.CGEventMaskBit(Quartz.kCGEventKeyUp)
            | Quartz.CGEventMaskBit(Quartz.kCGEventFlagsChanged)
        )

        self._tap = Quartz.CGEventTapCreate(
            Quartz.kCGSessionEventTap,
            Quartz.kCGHeadInsertEventTap,
            Quartz.kCGEventTapOptionListenOnly,
            mask,
            self._cg_callback,
            None,
        )

        if self._tap is None:
            print(
                "[vocalix] Failed to create event tap even though "
                "AXIsProcessTrusted returned True. Retrying in 2s...",
                flush=True,
            )
            threading.Timer(2.0, self._start_quartz).start()
            return

        source = Quartz.CFMachPortCreateRunLoopSource(None, self._tap, 0)

        def _run():
            self._run_loop_ref = Quartz.CFRunLoopGetCurrent()
            Quartz.CFRunLoopAddSource(
                self._run_loop_ref, source, Quartz.kCFRunLoopCommonModes,
            )
            Quartz.CGEventTapEnable(self._tap, True)
            Quartz.CFRunLoopRun()

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()

        self._start_watchdog()

    def _start_watchdog(self):
        """Re-enable the tap every 5 s in case macOS silently disabled it."""
        def _check():
            if self._tap is not None:
                if not Quartz.CGEventTapIsEnabled(self._tap):
                    print("[vocalix] Watchdog: tap was disabled — re-enabling", flush=True)
                    Quartz.CGEventTapEnable(self._tap, True)
                self._watchdog = threading.Timer(5.0, _check)
                self._watchdog.daemon = True
                self._watchdog.start()

        self._watchdog = threading.Timer(5.0, _check)
        self._watchdog.daemon = True
        self._watchdog.start()

    def _cg_callback(self, _proxy, event_type, event, _refcon):
        """CGEvent tap callback — runs on the tap thread, only reads
        integer key codes so it never touches TSM."""

        # macOS disables taps that are "too slow" — re-enable immediately
        if event_type == Quartz.kCGEventTapDisabledByTimeout:
            print("[vocalix] Event tap was disabled by timeout — re-enabling", flush=True)
            if self._tap is not None:
                Quartz.CGEventTapEnable(self._tap, True)
            return event

        if self._suppressed:
            return event

        keycode = Quartz.CGEventGetIntegerValueField(
            event, Quartz.kCGKeyboardEventKeycode,
        )

        target_codes = _MAC_VK.get(self._hotkey.lower(), ())
        if keycode not in target_codes:
            return event

        is_modifier = self._hotkey.lower() in _MODIFIER_KEYS

        if is_modifier:
            flags = Quartz.CGEventGetFlags(event)
            flag_bit = _MODIFIER_FLAG.get(self._hotkey.lower(), 0)
            pressed = bool(flags & flag_bit)
            if pressed and not self._key_held:
                self._key_held = True
                self._toggle()
            elif not pressed:
                self._key_held = False
        else:
            if event_type == Quartz.kCGEventKeyDown and not self._key_held:
                self._key_held = True
                self._toggle()
            elif event_type == Quartz.kCGEventKeyUp:
                self._key_held = False

        return event

    # -- Windows implementation --------------------------------------------

    def _on_press(self, _event):
        if self._suppressed:
            return
        self._toggle()

    # -- shared ------------------------------------------------------------

    def _toggle(self):
        if not self._recording:
            self._recording = True
            self.start_recording.emit()
        else:
            self._recording = False
            self.stop_recording.emit()
