import math

from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    pyqtSignal, pyqtProperty, QRectF,
)
from PyQt5.QtGui import QPainter, QColor, QPainterPath, QFont, QPen


class StateIndicator:
    IDLE = 0
    RECORDING = 1
    TRANSCRIBING = 2
    COMMANDING = 3


class FloatingPill(QWidget):

    MARGIN = 8
    PILL_H_INNER = 36
    PILL_H = PILL_H_INNER + MARGIN * 2

    IDLE_H_INNER = 14
    W_IDLE = 44
    W_RECORDING = 190
    W_TRANSCRIBING = 150
    W_COMMANDING = 150

    RADIUS = PILL_H_INNER // 2
    IDLE_RADIUS = IDLE_H_INNER // 2

    state_changed = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self._state = StateIndicator.IDLE
        self._drag_pos = None
        self._dot_count = 0
        self._wave_phase = 0.0
        self._pill_width = float(self.W_IDLE)

        self._setup_window()
        self._setup_timers()
        self._setup_animations()
        self._position_above_taskbar()

    # -- property for smooth width animation ------------------------------

    def _get_pill_width(self):
        return self._pill_width

    def _set_pill_width(self, val):
        self._pill_width = val
        total_w = int(val) + self.MARGIN * 2
        self.setFixedWidth(total_w)
        self._recentre_horizontally()
        self.update()

    animatedWidth = pyqtProperty(float, _get_pill_width, _set_pill_width)

    # -- setup ------------------------------------------------------------

    def _setup_window(self):
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(self.W_IDLE + self.MARGIN * 2, self.PILL_H)

    def _setup_timers(self):
        self._dot_timer = QTimer(self)
        self._dot_timer.setInterval(400)
        self._dot_timer.timeout.connect(self._tick_dots)

        self._wave_timer = QTimer(self)
        self._wave_timer.setInterval(45)
        self._wave_timer.timeout.connect(self._tick_wave)

    def _setup_animations(self):
        self._width_anim = QPropertyAnimation(self, b"animatedWidth")
        self._width_anim.setDuration(250)
        self._width_anim.setEasingCurve(QEasingCurve.OutCubic)

    def _position_above_taskbar(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = screen.height() - self.height() - 80
        self.move(x, y)
        self._screen_width = screen.width()
        self._base_y = y

    def _recentre_horizontally(self):
        x = (self._screen_width - self.width()) // 2
        self.move(x, self._base_y)

    # -- state transitions ------------------------------------------------

    def set_state(self, state: int):
        prev = self._state
        self._state = state

        self._dot_timer.stop()
        self._wave_timer.stop()

        if state == StateIndicator.IDLE:
            self._animate_width(self.W_IDLE)
        elif state == StateIndicator.RECORDING:
            self._dot_count = 0
            self._wave_phase = 0.0
            self._dot_timer.start()
            self._wave_timer.start()
            self._animate_width(self.W_RECORDING)
        elif state == StateIndicator.TRANSCRIBING:
            self._dot_count = 0
            self._dot_timer.start()
            self._animate_width(self.W_TRANSCRIBING)
        elif state == StateIndicator.COMMANDING:
            self._dot_count = 0
            self._dot_timer.start()
            self._animate_width(self.W_COMMANDING)

        self.state_changed.emit(state)
        self.update()

    def _animate_width(self, target: int):
        self._width_anim.stop()
        self._width_anim.setStartValue(self._pill_width)
        self._width_anim.setEndValue(float(target))
        self._width_anim.start()

    # -- tick callbacks ---------------------------------------------------

    def _tick_dots(self):
        self._dot_count = (self._dot_count % 3) + 1
        self.update()

    def _tick_wave(self):
        self._wave_phase += 0.25
        self.update()

    # -- painting ---------------------------------------------------------

    def _pill_rect(self) -> QRectF:
        m = self.MARGIN
        if self._state == StateIndicator.IDLE:
            h = self.IDLE_H_INNER
            y = m + (self.PILL_H_INNER - h) / 2
            return QRectF(m, y, self.width() - m * 2, h)
        return QRectF(m, m, self.width() - m * 2, self.PILL_H_INNER)

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        pr = self._pill_rect()
        r = self.IDLE_RADIUS if self._state == StateIndicator.IDLE else self.RADIUS

        # Subtle shadow
        shadow_path = QPainterPath()
        shadow_path.addRoundedRect(pr.adjusted(-1, 1, 1, 2), r, r)
        p.fillPath(shadow_path, QColor(0, 0, 0, 30))

        # Pill body
        body = QPainterPath()
        body.addRoundedRect(pr, r, r)
        p.fillPath(body, QColor(255, 255, 255, 245))

        border_pen = QPen(QColor(190, 190, 190, 140), 1.0)
        p.setPen(border_pen)
        p.drawPath(body)

        # Content
        if self._state == StateIndicator.IDLE:
            self._draw_idle_line(p, pr)
        elif self._state == StateIndicator.RECORDING:
            self._draw_recording(p, pr)
        elif self._state == StateIndicator.TRANSCRIBING:
            self._draw_transcribing(p, pr)
        elif self._state == StateIndicator.COMMANDING:
            self._draw_commanding(p, pr)

        p.end()

    def _draw_idle_line(self, p: QPainter, pr: QRectF):
        """Tiny horizontal dash in the centre of the slim capsule."""
        cx = pr.x() + pr.width() / 2
        cy = pr.y() + pr.height() / 2
        dash_w = 14
        dash_h = 2.2
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(60, 60, 65, 180))
        p.drawRoundedRect(
            QRectF(cx - dash_w / 2, cy - dash_h / 2, dash_w, dash_h),
            1.0, 1.0,
        )

    def _draw_recording(self, p: QPainter, pr: QRectF):
        """Animated waveform + 'I'm listening' with cycling dots."""
        # Animated waveform bars on the left
        wave_x = pr.x() + 16
        cy = pr.y() + pr.height() / 2
        bar_w = 2.5
        gap = 3.5
        num_bars = 5
        for i in range(num_bars):
            phase = self._wave_phase + i * 0.7
            h = 6 + 8 * abs(math.sin(phase))
            bx = wave_x + i * (bar_w + gap)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(50, 50, 55))
            p.drawRoundedRect(QRectF(bx, cy - h / 2, bar_w, h), 1.2, 1.2)

        # Text — premium serif italic like Whispr Flow / Apple
        dots = "." * self._dot_count
        text = f"I\u2019m listening{dots}"
        p.setPen(QColor(30, 30, 32))
        font = QFont("Georgia", 11)
        font.setItalic(True)
        p.setFont(font)
        text_x = wave_x + num_bars * (bar_w + gap) + 8
        text_rect = QRectF(text_x, pr.y(), pr.right() - text_x - 8, pr.height())
        p.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, text)

    def _draw_transcribing(self, p: QPainter, pr: QRectF):
        dots = "." * self._dot_count
        text = f"Thinking{dots}"
        p.setPen(QColor(30, 30, 32))
        font = QFont("Georgia", 11)
        font.setItalic(True)
        p.setFont(font)
        p.drawText(pr, Qt.AlignCenter, text)

    def _draw_commanding(self, p: QPainter, pr: QRectF):
        dots = "." * self._dot_count
        text = f"Writing{dots}"
        p.setPen(QColor(30, 30, 32))
        font = QFont("Georgia", 11)
        font.setItalic(True)
        p.setFont(font)
        p.drawText(pr, Qt.AlignCenter, text)

    # -- dragging ---------------------------------------------------------

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.LeftButton:
            new_pos = event.globalPos() - self._drag_pos
            self.move(new_pos)
            self._base_y = new_pos.y()
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
