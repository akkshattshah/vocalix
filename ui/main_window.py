import sys
import os

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QApplication,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QKeyEvent, QPixmap

from auth.session import load_session, clear_session
from core.config import get_hotkey, set_hotkey

_IS_MAC = sys.platform == "darwin"
_FONT_MONO = "Menlo" if _IS_MAC else "Consolas"
_FONT_UI = ".AppleSystemUIFont" if _IS_MAC else "Segoe UI"


def _resource_path(relative: str) -> str:
    if getattr(sys, "_MEIPASS", None):
        return os.path.join(sys._MEIPASS, relative)
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)


class HotkeyCapture(QLabel):
    """A styled label that captures a single key press when in capture mode."""

    hotkey_changed = pyqtSignal(str)

    def __init__(self, current_key: str):
        super().__init__()
        self._capturing = False
        self._key = current_key
        self._update_display()
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(44)
        self.setFocusPolicy(Qt.StrongFocus)
        self._apply_style(False)

    def _apply_style(self, capturing: bool):
        border_color = "#1a1a1a" if capturing else "#ccc"
        bg = "#f0f0f0" if not capturing else "#fff"
        self.setStyleSheet(
            f"QLabel {{ background: {bg}; border: 2px solid {border_color}; "
            f"border-radius: 10px; padding: 0 16px; }}"
        )

    def _update_display(self):
        display = self._key.upper() if self._key else "—"
        font = QFont(_FONT_MONO, 14)
        font.setBold(True)
        self.setFont(font)
        self.setText(display)

    def start_capture(self):
        self._capturing = True
        self._apply_style(True)
        font = QFont("Georgia", 11)
        font.setItalic(True)
        self.setFont(font)
        self.setText("Press any key…")
        self.setFocus()

    def keyPressEvent(self, event: QKeyEvent):
        if not self._capturing:
            return super().keyPressEvent(event)

        key = event.key()
        if key == Qt.Key_unknown:
            return

        name = _qt_key_to_keyboard_name(key)
        if name:
            self._key = name
            self._capturing = False
            self._apply_style(False)
            self._update_display()
            self.hotkey_changed.emit(name)

    def current_key(self) -> str:
        return self._key


_META_NAME = "cmd" if _IS_MAC else "windows"

_QT_KEY_MAP = {
    Qt.Key_Control: "ctrl", Qt.Key_Shift: "shift", Qt.Key_Alt: "alt",
    Qt.Key_Meta: _META_NAME, Qt.Key_Super_L: _META_NAME, Qt.Key_Super_R: _META_NAME,
    Qt.Key_F1: "f1", Qt.Key_F2: "f2", Qt.Key_F3: "f3", Qt.Key_F4: "f4",
    Qt.Key_F5: "f5", Qt.Key_F6: "f6", Qt.Key_F7: "f7", Qt.Key_F8: "f8",
    Qt.Key_F9: "f9", Qt.Key_F10: "f10", Qt.Key_F11: "f11", Qt.Key_F12: "f12",
    Qt.Key_Space: "space", Qt.Key_Return: "enter", Qt.Key_Escape: "esc",
    Qt.Key_Tab: "tab", Qt.Key_Backspace: "backspace", Qt.Key_Delete: "delete",
    Qt.Key_Insert: "insert", Qt.Key_Home: "home", Qt.Key_End: "end",
    Qt.Key_PageUp: "page up", Qt.Key_PageDown: "page down",
    Qt.Key_Up: "up", Qt.Key_Down: "down", Qt.Key_Left: "left", Qt.Key_Right: "right",
    Qt.Key_CapsLock: "caps lock", Qt.Key_NumLock: "num lock",
    Qt.Key_ScrollLock: "scroll lock", Qt.Key_Pause: "pause",
    Qt.Key_Print: "print screen",
}


def _qt_key_to_keyboard_name(qt_key: int) -> str | None:
    if qt_key in _QT_KEY_MAP:
        return _QT_KEY_MAP[qt_key]
    if Qt.Key_A <= qt_key <= Qt.Key_Z:
        return chr(qt_key).lower()
    if Qt.Key_0 <= qt_key <= Qt.Key_9:
        return chr(qt_key)
    ch = chr(qt_key) if 0x20 <= qt_key <= 0x7E else None
    return ch


class MainWindow(QMainWindow):
    """Settings / home window for Vocalix."""

    hotkey_updated = pyqtSignal(str)
    capture_started = pyqtSignal()
    signed_out = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vocalix")
        self.setFixedSize(420, 380)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)

        logo_path = _resource_path("logo.png")
        if os.path.exists(logo_path):
            self.setWindowIcon(QIcon(logo_path))

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(36, 30, 36, 24)
        layout.setSpacing(0)

        # --- Header ---
        logo_label = QLabel()
        if os.path.exists(logo_path):
            pix = QPixmap(logo_path).scaledToHeight(36, Qt.SmoothTransformation)
            logo_label.setPixmap(pix)
        logo_label.setAlignment(Qt.AlignLeft)
        layout.addWidget(logo_label)
        layout.addSpacing(12)

        session = load_session()
        user = session.get("user", {}) if session else {}
        name = (user.get("user_metadata", {}).get("full_name")
                or user.get("email", ""))

        welcome = QLabel(f"Welcome, {name}" if name else "Welcome")
        wfont = QFont("Georgia", 15)
        wfont.setItalic(True)
        welcome.setFont(wfont)
        welcome.setStyleSheet("color: #1a1a1a; margin-bottom: 4px;")
        layout.addWidget(welcome)

        layout.addSpacing(24)

        # --- Hotkey section ---
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setStyleSheet("color: #e0e0e0;")
        layout.addWidget(sep1)
        layout.addSpacing(16)

        hk_title = QLabel("Activation Key")
        hk_title.setFont(QFont(_FONT_UI, 10))
        hk_title.setStyleSheet("color: #555;")
        layout.addWidget(hk_title)
        layout.addSpacing(6)

        hk_row = QHBoxLayout()
        hk_row.setSpacing(12)

        self._hotkey_capture = HotkeyCapture(get_hotkey())
        self._hotkey_capture.hotkey_changed.connect(self._on_hotkey_changed)
        hk_row.addWidget(self._hotkey_capture, stretch=1)

        change_btn = QPushButton("Change")
        change_btn.setFont(QFont(_FONT_UI, 10))
        change_btn.setCursor(Qt.PointingHandCursor)
        change_btn.setFixedHeight(44)
        change_btn.setFixedWidth(90)
        change_btn.setStyleSheet(
            "QPushButton { background: #1a1a1a; color: white; border: none; "
            "border-radius: 10px; }"
            "QPushButton:hover { background: #333; }"
        )
        change_btn.clicked.connect(self._on_start_capture)
        hk_row.addWidget(change_btn)

        layout.addLayout(hk_row)

        hk_hint = QLabel("Press the key you want to use as your speech toggle.")
        hk_hint.setFont(QFont(_FONT_UI, 8))
        hk_hint.setStyleSheet("color: #999; margin-top: 4px;")
        layout.addWidget(hk_hint)

        layout.addStretch()

        # --- Footer ---
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("color: #e0e0e0;")
        layout.addWidget(sep2)
        layout.addSpacing(10)

        footer = QHBoxLayout()

        signout_btn = QPushButton("Sign out")
        signout_btn.setFont(QFont(_FONT_UI, 9))
        signout_btn.setCursor(Qt.PointingHandCursor)
        signout_btn.setFlat(True)
        signout_btn.setStyleSheet(
            "QPushButton { color: #999; border: none; padding: 0; }"
            "QPushButton:hover { color: #333; }"
        )
        signout_btn.clicked.connect(self._on_sign_out)
        footer.addWidget(signout_btn)

        footer.addStretch()

        version = QLabel("v1.0.0")
        version.setFont(QFont(_FONT_UI, 8))
        version.setStyleSheet("color: #bbb;")
        footer.addWidget(version)

        layout.addLayout(footer)

        self.setStyleSheet("QMainWindow { background: #ffffff; }")
        self._center_on_screen()

    def _center_on_screen(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def _on_start_capture(self):
        self.capture_started.emit()
        self._hotkey_capture.start_capture()

    def _on_hotkey_changed(self, new_key: str):
        set_hotkey(new_key)
        self.hotkey_updated.emit(new_key)

    def _on_sign_out(self):
        clear_session()
        self.signed_out.emit()

    def closeEvent(self, event):
        QApplication.instance().quit()
