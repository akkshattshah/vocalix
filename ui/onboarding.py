"""Three-step onboarding wizard shown once to new users."""

import sys
import os

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QStackedWidget, QApplication,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QPixmap

from ui.main_window import HotkeyCapture
from core.config import get_hotkey, set_hotkey, set_onboarded

_IS_MAC = sys.platform == "darwin"
_FONT_UI = ".AppleSystemUIFont" if _IS_MAC else "Segoe UI"

_BTN_STYLE = (
    "QPushButton { background: #1a1a1a; color: white; border: none; "
    "border-radius: 10px; padding: 10px 32px; }"
    "QPushButton:hover { background: #333; }"
    "QPushButton:disabled { background: #ccc; color: #888; }"
)

_CHANGE_BTN_STYLE = (
    "QPushButton { background: #1a1a1a; color: white; border: none; "
    "border-radius: 10px; }"
    "QPushButton:hover { background: #333; }"
)

_PLAYGROUND_STYLE = (
    "QTextEdit { background: #f8f8f8; border: 2px solid #e0e0e0; "
    "border-radius: 10px; padding: 12px; font-family: Georgia; "
    "font-size: 12px; color: #222; }"
    "QTextEdit:focus { border-color: #1a1a1a; }"
)


def _resource_path(relative: str) -> str:
    if getattr(sys, "_MEIPASS", None):
        return os.path.join(sys._MEIPASS, relative)
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)


class OnboardingWizard(QWidget):
    """Mandatory 3-step onboarding: set hotkey, try transcription, try command."""

    finished = pyqtSignal()
    hotkey_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vocalix — Get Started")
        self.setFixedSize(480, 440)
        self.setWindowFlags(
            Qt.WindowCloseButtonHint | Qt.WindowTitleHint
        )
        self.setStyleSheet("background: #ffffff;")

        icon_path = _resource_path("icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        root = QVBoxLayout(self)
        root.setContentsMargins(36, 28, 36, 24)
        root.setSpacing(0)

        # Step indicator
        self._step_label = QLabel("1 / 3")
        self._step_label.setFont(QFont(_FONT_UI, 9))
        self._step_label.setStyleSheet("color: #bbb;")
        self._step_label.setAlignment(Qt.AlignRight)
        root.addWidget(self._step_label)
        root.addSpacing(4)

        # Stacked pages
        self._stack = QStackedWidget()
        root.addWidget(self._stack)

        self._build_step1()
        self._build_step2()
        self._build_step3()

        self._stack.setCurrentIndex(0)
        self._center_on_screen()

    # -- Step 1: Hotkey --------------------------------------------------------

    def _build_step1(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        heading = QLabel("Choose your activation key")
        hfont = QFont("Georgia", 18)
        hfont.setItalic(True)
        heading.setFont(hfont)
        heading.setStyleSheet("color: #1a1a1a;")
        heading.setWordWrap(True)
        lay.addWidget(heading)
        lay.addSpacing(8)

        desc = QLabel(
            "This is the key you\u2019ll press to start and stop recording.\n"
            "Press Change, then press the key you want to use."
        )
        desc.setFont(QFont(_FONT_UI, 10))
        desc.setStyleSheet("color: #666;")
        desc.setWordWrap(True)
        lay.addWidget(desc)
        lay.addSpacing(24)

        hk_row = QHBoxLayout()
        hk_row.setSpacing(12)

        self._hk_capture = HotkeyCapture(get_hotkey())
        self._hk_capture.hotkey_changed.connect(self._on_hotkey_set)
        hk_row.addWidget(self._hk_capture, stretch=1)

        change_btn = QPushButton("Change")
        change_btn.setFont(QFont(_FONT_UI, 10))
        change_btn.setCursor(Qt.PointingHandCursor)
        change_btn.setFixedHeight(44)
        change_btn.setFixedWidth(90)
        change_btn.setStyleSheet(_CHANGE_BTN_STYLE)
        change_btn.clicked.connect(self._hk_capture.start_capture)
        hk_row.addWidget(change_btn)

        lay.addLayout(hk_row)
        lay.addStretch()

        self._step1_next = QPushButton("Next")
        self._step1_next.setFont(QFont(_FONT_UI, 11))
        self._step1_next.setCursor(Qt.PointingHandCursor)
        self._step1_next.setStyleSheet(_BTN_STYLE)
        self._step1_next.clicked.connect(self._go_step2)
        lay.addWidget(self._step1_next, alignment=Qt.AlignRight)

        self._stack.addWidget(page)

    def _on_hotkey_set(self, name: str):
        set_hotkey(name)
        self.hotkey_changed.emit(name)

    def _go_step2(self):
        self._stack.setCurrentIndex(1)
        self._step_label.setText("2 / 3")

    # -- Step 2: Speech-to-Text playground ------------------------------------

    def _build_step2(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        heading = QLabel("Try it out")
        hfont = QFont("Georgia", 18)
        hfont.setItalic(True)
        heading.setFont(hfont)
        heading.setStyleSheet("color: #1a1a1a;")
        lay.addWidget(heading)
        lay.addSpacing(8)

        desc = QLabel(
            "Click in the box below, press your hotkey, say something,\n"
            "then press the hotkey again. Your words will appear as text."
        )
        desc.setFont(QFont(_FONT_UI, 10))
        desc.setStyleSheet("color: #666;")
        desc.setWordWrap(True)
        lay.addWidget(desc)
        lay.addSpacing(16)

        self._playground1 = QTextEdit()
        self._playground1.setPlaceholderText("Your transcription will appear here\u2026")
        self._playground1.setFixedHeight(140)
        self._playground1.setStyleSheet(_PLAYGROUND_STYLE)
        self._playground1.textChanged.connect(self._check_step2)
        lay.addWidget(self._playground1)

        lay.addStretch()

        self._step2_next = QPushButton("Next")
        self._step2_next.setFont(QFont(_FONT_UI, 11))
        self._step2_next.setCursor(Qt.PointingHandCursor)
        self._step2_next.setStyleSheet(_BTN_STYLE)
        self._step2_next.setEnabled(False)
        self._step2_next.clicked.connect(self._go_step3)
        lay.addWidget(self._step2_next, alignment=Qt.AlignRight)

        self._stack.addWidget(page)

    def _check_step2(self):
        has_text = bool(self._playground1.toPlainText().strip())
        self._step2_next.setEnabled(has_text)

    def _go_step3(self):
        self._playground1.clear()
        self._stack.setCurrentIndex(2)
        self._step_label.setText("3 / 3")
        self._playground2.setFocus()

    # -- Step 3: Hey Vocalix playground ---------------------------------------

    def _build_step3(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        heading = QLabel("Give it a command")
        hfont = QFont("Georgia", 18)
        hfont.setItalic(True)
        heading.setFont(hfont)
        heading.setStyleSheet("color: #1a1a1a;")
        lay.addWidget(heading)
        lay.addSpacing(8)

        desc = QLabel(
            "Click in the box, press your hotkey, say:\n"
            "\u201cHey Vocalix, write a mail to my boss saying\n"
            "I won\u2019t be coming to office for the next one week\u201d\n"
            "then press hotkey again. The AI will write it for you."
        )
        desc.setFont(QFont(_FONT_UI, 10))
        desc.setStyleSheet("color: #666;")
        desc.setWordWrap(True)
        lay.addWidget(desc)
        lay.addSpacing(16)

        self._playground2 = QTextEdit()
        self._playground2.setPlaceholderText("AI-generated text will appear here\u2026")
        self._playground2.setFixedHeight(140)
        self._playground2.setStyleSheet(_PLAYGROUND_STYLE)
        self._playground2.textChanged.connect(self._check_step3)
        lay.addWidget(self._playground2)

        lay.addStretch()

        self._done_btn = QPushButton("Done")
        self._done_btn.setFont(QFont(_FONT_UI, 11))
        self._done_btn.setCursor(Qt.PointingHandCursor)
        self._done_btn.setStyleSheet(_BTN_STYLE)
        self._done_btn.setEnabled(False)
        self._done_btn.clicked.connect(self._on_done)
        lay.addWidget(self._done_btn, alignment=Qt.AlignRight)

        self._stack.addWidget(page)

    def _check_step3(self):
        has_text = bool(self._playground2.toPlainText().strip())
        self._done_btn.setEnabled(has_text)

    def _on_done(self):
        set_onboarded(True)
        self.finished.emit()
        self.close()

    # -- Helpers ---------------------------------------------------------------

    def _center_on_screen(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def closeEvent(self, event):
        if not self._done_btn.isEnabled():
            event.ignore()
            return
        event.accept()
