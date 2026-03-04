"""Native macOS overlay using NSPanel via PyObjC.

Bypasses Qt's window management entirely so that macOS correctly
honours canJoinAllSpaces + fullScreenAuxiliary on the panel.
"""

import math
import objc
from AppKit import (
    NSPanel, NSView, NSColor, NSFont, NSBezierPath,
    NSAttributedString, NSMutableParagraphStyle,
    NSBackingStoreBuffered, NSScreen,
    NSFontAttributeName, NSForegroundColorAttributeName,
    NSParagraphStyleAttributeName,
)
from Foundation import NSMakeRect

NSBorderlessWindowMask = 0
NSNonactivatingPanelMask = 1 << 7

_MARGIN = 8
_PILL_H_INNER = 36
_PILL_H = _PILL_H_INNER + _MARGIN * 2
_IDLE_H_INNER = 14
_IDLE_RADIUS = _IDLE_H_INNER // 2
_RADIUS = _PILL_H_INNER // 2

_BODY_COLOR = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, 1, 1, 0.96)
_SHADOW_COLOR = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, 0.12)
_BORDER_COLOR = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.745, 0.745, 0.745, 0.55)
_BAR_COLOR = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.196, 0.196, 0.216, 1.0)
_DASH_COLOR = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.235, 0.235, 0.255, 0.7)
_TEXT_COLOR = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.118, 0.118, 0.125, 1.0)


def _italic_font():
    f = NSFont.fontWithName_size_("Georgia-Italic", 11)
    if f is None:
        f = NSFont.fontWithName_size_("Georgia", 11)
    if f is None:
        f = NSFont.systemFontOfSize_(11)
    return f


class PillView(NSView):
    """Custom NSView that draws the pill overlay content."""

    def initWithFrame_(self, frame):
        self = objc.super(PillView, self).initWithFrame_(frame)
        if self is not None:
            self._state = 0
            self._dot_count = 0
            self._wave_phase = 0.0
        return self

    def isFlipped(self):
        return True

    def isOpaque(self):
        return False

    # -- main draw ---------------------------------------------------------

    def drawRect_(self, dirtyRect):
        NSColor.clearColor().set()
        NSBezierPath.fillRect_(self.bounds())

        bounds = self.bounds()
        m = _MARGIN

        if self._state == 0:
            h = _IDLE_H_INNER
            r = _IDLE_RADIUS
            y = m + (_PILL_H_INNER - h) / 2
            pr = NSMakeRect(m, y, bounds.size.width - m * 2, h)
        else:
            h = _PILL_H_INNER
            r = _RADIUS
            pr = NSMakeRect(m, m, bounds.size.width - m * 2, h)

        sr = NSMakeRect(
            pr.origin.x - 1, pr.origin.y + 1,
            pr.size.width + 2, pr.size.height + 1,
        )
        shadow = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(sr, r, r)
        _SHADOW_COLOR.set()
        shadow.fill()

        body = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(pr, r, r)
        _BODY_COLOR.set()
        body.fill()
        _BORDER_COLOR.set()
        body.setLineWidth_(1.0)
        body.stroke()

        if self._state == 0:
            self._draw_idle(pr)
        elif self._state == 1:
            self._draw_recording(pr)
        elif self._state == 2:
            self._draw_label("Thinking", pr)
        elif self._state == 3:
            self._draw_label("Writing", pr)

    # -- state renderers ---------------------------------------------------

    def _draw_idle(self, pr):
        cx = pr.origin.x + pr.size.width / 2
        cy = pr.origin.y + pr.size.height / 2
        dw, dh = 14, 2.2
        dash = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            NSMakeRect(cx - dw / 2, cy - dh / 2, dw, dh), 1, 1,
        )
        _DASH_COLOR.set()
        dash.fill()

    def _draw_recording(self, pr):
        wave_x = pr.origin.x + 16
        cy = pr.origin.y + pr.size.height / 2
        bar_w, gap, num_bars = 2.5, 3.5, 5

        _BAR_COLOR.set()
        for i in range(num_bars):
            phase = self._wave_phase + i * 0.7
            h = 6 + 8 * abs(math.sin(phase))
            bx = wave_x + i * (bar_w + gap)
            bar = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
                NSMakeRect(bx, cy - h / 2, bar_w, h), 1.2, 1.2,
            )
            bar.fill()

        dots = "." * self._dot_count
        text_x = wave_x + num_bars * (bar_w + gap) + 8
        w = pr.origin.x + pr.size.width - text_x - 8
        self._draw_text(
            f"I\u2019m listening{dots}",
            text_x, pr.origin.y, w, pr.size.height,
        )

    def _draw_label(self, base, pr):
        dots = "." * self._dot_count
        self._draw_text(
            f"{base}{dots}",
            pr.origin.x, pr.origin.y, pr.size.width, pr.size.height,
            center=True,
        )

    @staticmethod
    def _draw_text(text, x, y, w, h, center=False):
        ps = NSMutableParagraphStyle.alloc().init()
        ps.setAlignment_(1 if center else 0)

        attrs = {
            NSFontAttributeName: _italic_font(),
            NSForegroundColorAttributeName: _TEXT_COLOR,
            NSParagraphStyleAttributeName: ps,
        }
        ns_str = NSAttributedString.alloc().initWithString_attributes_(text, attrs)
        sz = ns_str.size()
        draw_y = y + (h - sz.height) / 2
        ns_str.drawInRect_(NSMakeRect(x, draw_y, w, sz.height))


# ---------------------------------------------------------------------------
# Panel factory
# ---------------------------------------------------------------------------

def create_pill_panel(cocoa_x, cocoa_y, w, h):
    """Create an NSPanel with the correct overlay properties.

    Coordinates must be in Cocoa screen space (origin = bottom-left).
    Returns (panel, pill_view).
    """
    kCanJoinAllSpaces = 1 << 0
    kFullScreenAuxiliary = 1 << 8

    panel = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
        NSMakeRect(cocoa_x, cocoa_y, w, h),
        NSBorderlessWindowMask | NSNonactivatingPanelMask,
        NSBackingStoreBuffered,
        False,
    )

    panel.setLevel_(1000)
    panel.setCollectionBehavior_(kCanJoinAllSpaces | kFullScreenAuxiliary)
    panel.setHidesOnDeactivate_(False)
    panel.setOpaque_(False)
    panel.setBackgroundColor_(NSColor.clearColor())
    panel.setHasShadow_(False)
    panel.setMovableByWindowBackground_(True)

    view = PillView.alloc().initWithFrame_(NSMakeRect(0, 0, w, h))
    panel.setContentView_(view)

    return panel, view
