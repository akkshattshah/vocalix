import sys

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

_IS_MAC = sys.platform == "darwin"
_FONT_MONO = "Menlo" if _IS_MAC else "Consolas"
_FONT_UI = ".AppleSystemUIFont" if _IS_MAC else "Segoe UI"


class ApiKeyDialog(QDialog):
    """First-run dialog that asks the user for their OpenAI API key."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Vocalix Setup")
        self.setFixedSize(460, 240)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        self._key = ""
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 24)
        layout.setSpacing(12)

        heading = QLabel("Welcome to Vocalix")
        heading_font = QFont("Georgia", 16)
        heading_font.setItalic(True)
        heading.setFont(heading_font)
        heading.setAlignment(Qt.AlignCenter)
        layout.addWidget(heading)

        desc = QLabel("Enter your OpenAI API key to get started.\n"
                       "You can find it at platform.openai.com/api-keys")
        desc.setFont(QFont(_FONT_UI, 9))
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #666;")
        layout.addWidget(desc)

        layout.addSpacing(4)

        self._input = QLineEdit()
        self._input.setPlaceholderText("sk-proj-...")
        self._input.setEchoMode(QLineEdit.Password)
        self._input.setFont(QFont(_FONT_MONO, 10))
        self._input.setStyleSheet(
            "QLineEdit { padding: 8px 12px; border: 1px solid #ccc; "
            "border-radius: 8px; background: #fafafa; }"
            "QLineEdit:focus { border-color: #333; }"
        )
        layout.addWidget(self._input)

        layout.addSpacing(4)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self._save_btn = QPushButton("Continue")
        self._save_btn.setFont(QFont(_FONT_UI, 10))
        self._save_btn.setCursor(Qt.PointingHandCursor)
        self._save_btn.setStyleSheet(
            "QPushButton { padding: 8px 28px; border-radius: 8px; "
            "background: #1a1a1a; color: white; border: none; }"
            "QPushButton:hover { background: #333; }"
        )
        self._save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(self._save_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self._input.returnPressed.connect(self._on_save)

    def _on_save(self):
        key = self._input.text().strip()
        if key:
            self._key = key
            self.accept()

    def get_key(self) -> str:
        return self._key
