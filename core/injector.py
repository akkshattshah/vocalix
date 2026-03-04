import sys
import time
import subprocess

_IS_WIN = sys.platform == "win32"
_IS_MAC = sys.platform == "darwin"


# ---------------------------------------------------------------------------
# Windows clipboard via Win32 API
# ---------------------------------------------------------------------------
if _IS_WIN:
    import ctypes
    import ctypes.wintypes as w
    import pyautogui

    CF_UNICODETEXT = 13
    GMEM_MOVEABLE = 0x0002

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    kernel32.GlobalAlloc.argtypes = [w.UINT, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalUnlock.restype = w.BOOL
    user32.OpenClipboard.argtypes = [w.HWND]
    user32.OpenClipboard.restype = w.BOOL
    user32.CloseClipboard.argtypes = []
    user32.CloseClipboard.restype = w.BOOL
    user32.EmptyClipboard.argtypes = []
    user32.EmptyClipboard.restype = w.BOOL
    user32.SetClipboardData.argtypes = [w.UINT, ctypes.c_void_p]
    user32.SetClipboardData.restype = ctypes.c_void_p
    user32.GetClipboardData.argtypes = [w.UINT]
    user32.GetClipboardData.restype = ctypes.c_void_p

    def _clipboard_set(text: str):
        encoded = text.encode("utf-16-le") + b"\x00\x00"
        user32.OpenClipboard(None)
        user32.EmptyClipboard()
        h = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(encoded))
        ptr = kernel32.GlobalLock(h)
        ctypes.memmove(ptr, encoded, len(encoded))
        kernel32.GlobalUnlock(h)
        user32.SetClipboardData(CF_UNICODETEXT, h)
        user32.CloseClipboard()

    def _clipboard_get() -> str | None:
        try:
            user32.OpenClipboard(None)
            h = user32.GetClipboardData(CF_UNICODETEXT)
            if not h:
                user32.CloseClipboard()
                return None
            ptr = kernel32.GlobalLock(h)
            text = ctypes.wstring_at(ptr)
            kernel32.GlobalUnlock(h)
            user32.CloseClipboard()
            return text
        except Exception:
            try:
                user32.CloseClipboard()
            except Exception:
                pass
            return None

    def _paste():
        pyautogui.hotkey("ctrl", "v")


# ---------------------------------------------------------------------------
# macOS clipboard via pbcopy / pbpaste  +  pynput for Cmd-V
# ---------------------------------------------------------------------------
elif _IS_MAC:
    from pynput.keyboard import Controller as _KbController, Key as _Key

    _mac_kb = _KbController()

    def _clipboard_set(text: str):
        subprocess.run(
            ["/usr/bin/pbcopy"], input=text.encode("utf-8"), check=True,
        )

    def _clipboard_get() -> str | None:
        try:
            r = subprocess.run(
                ["/usr/bin/pbpaste"], capture_output=True, check=True,
            )
            return r.stdout.decode("utf-8")
        except Exception:
            return None

    def _paste():
        _mac_kb.press(_Key.cmd)
        _mac_kb.press("v")
        _mac_kb.release("v")
        _mac_kb.release(_Key.cmd)

else:
    raise RuntimeError(f"Unsupported platform: {sys.platform}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def inject_text(text: str):
    """Paste *text* into the focused text field via clipboard + shortcut."""
    if _IS_WIN:
        text = text.replace("\r\n", "\n").replace("\n", "\r\n")

    original = _clipboard_get()
    _clipboard_set(text)

    time.sleep(0.05)
    _paste()
    time.sleep(0.15)

    if original is not None:
        time.sleep(0.10)
        _clipboard_set(original)
