"""Small reusable widgets: elided label and a base-coloured sequence viewer."""
import math
import re

from frontend.ui.qt_compat import (
    QFrame, QLabel, QPlainTextEdit, QPushButton, QWidget, QColor, QPainter, QPen, QBrush, QFont,
    QRectF, QPointF, QPainterPath, QLinearGradient, antialias_hint, no_pen, align_left, align_center,
)
from frontend.ui.qt_extra import get_qt, enum
from frontend.ui.charts import HelixWidget
from frontend.ui.theme import BASE_TEXT, BG_BOTTOM, BG_TOP, FONT_UI, NAVY

QSize = get_qt("QSize")
QPixmap = get_qt("QPixmap")
QIcon = get_qt("QIcon")
QSyntaxHighlighter = get_qt("QSyntaxHighlighter")
QTextCharFormat = get_qt("QTextCharFormat")
Qt = get_qt("Qt")


class ElidedLabel(QLabel):
    """A label that shortens its text with "..." instead of forcing the window wider."""

    def __init__(self, text: str = "", parent=None):
        super().__init__(parent)
        self._full_text = ""
        self.setMinimumWidth(0)
        self.setText(text)

    def setText(self, text: str):
        self._full_text = text
        self.setToolTip(text)
        self._refresh()

    def text(self) -> str:
        return self._full_text

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._refresh()

    def minimumSizeHint(self):
        return QSize(0, super().minimumSizeHint().height())

    def sizeHint(self):
        base = super().sizeHint()
        margins = self.contentsMargins()
        width = self.fontMetrics().horizontalAdvance(self._full_text) + margins.left() + margins.right() + 4
        return QSize(width, base.height())

    def _refresh(self):
        mode = enum(Qt, "TextElideMode", "ElideRight")
        shown = self.fontMetrics().elidedText(self._full_text, mode, max(10, self.width() - 2))
        super().setText(shown)


class BaseHighlighter(QSyntaxHighlighter):
    _RUNS = re.compile(r"A+|T+|U+|G+|C+|N+", re.IGNORECASE)

    def __init__(self, document):
        super().__init__(document)
        self._formats = {}
        for letter, colour in BASE_TEXT.items():
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(colour))
            bold = enum(QFont, "Weight", "Bold")
            fmt.setFontWeight(int(getattr(bold, "value", bold)))
            self._formats[letter] = fmt

    def highlightBlock(self, text):
        for match in self._RUNS.finditer(text):
            fmt = self._formats.get(match.group(0)[0].upper())
            if fmt is not None:
                self.setFormat(match.start(), match.end() - match.start(), fmt)


class SequenceView(QPlainTextEdit):
    """Read-only monospace viewer. Bases A/T/U/G/C/N are coloured to match the charts.

    Its height follows the amount of text (between a minimum and a maximum), so short
    results do not leave an empty box and long ones scroll inside it.
    """

    def __init__(self, highlight: bool = True, parent=None, min_height: int = 64, max_height: int = 320):
        super().__init__(parent)
        self.setProperty("class", "SeqBox")
        self.setReadOnly(True)
        self.setLineWrapMode(enum(QPlainTextEdit, "LineWrapMode", "NoWrap"))
        self._highlighter = BaseHighlighter(self.document()) if highlight else None
        self._min_h = int(min_height)
        self._max_h = int(max_height)
        self.textChanged.connect(self.fit_to_content)
        self.fit_to_content()

    def set_height_limits(self, min_height: int, max_height: int):
        self._min_h, self._max_h = int(min_height), int(max_height)
        self.fit_to_content()

    def fit_to_content(self):
        lines = max(1, self.document().blockCount())
        wanted = lines * self.fontMetrics().lineSpacing() + 18 + 16 + 14  # padding, border, scrollbar
        self.setFixedHeight(max(self._min_h, min(self._max_h, int(wanted))))

    def showEvent(self, event):
        super().showEvent(event)
        self.fit_to_content()


def draw_nav_icon(p, key, cx, cy, colour, width=1.7):
    """Tiny line icons for the sidebar, drawn with the painter so they stay crisp and recolourable."""
    pen = QPen(QColor(colour), width)
    pen.setCapStyle(enum(Qt, "PenCapStyle", "RoundCap"))
    pen.setJoinStyle(enum(Qt, "PenJoinStyle", "RoundJoin"))
    p.setPen(pen)
    p.setBrush(QBrush())

    def line(x1, y1, x2, y2):
        p.drawLine(QPointF(cx + x1, cy + y1), QPointF(cx + x2, cy + y2))

    if key == "overview":
        for dx in (-7, 1):
            for dy in (-7, 1):
                p.drawRoundedRect(QRectF(cx + dx, cy + dy, 6, 6), 1.5, 1.5)
    elif key == "gc":
        line(-8, 4, -3, -2)
        line(-3, -2, 1, 2)
        line(1, 2, 8, -6)
    elif key == "compress":
        line(-8, -5, -2, 0)
        line(-2, 0, -8, 5)
        line(8, -5, 2, 0)
        line(2, 0, 8, 5)
    elif key == "revcomp":
        line(-8, -3, 8, -3)
        line(8, -3, 4, -6)
        line(8, -3, 4, 0)
        line(8, 3, -8, 3)
        line(-8, 3, -4, 0)
        line(-8, 3, -4, 6)
    elif key == "rna":
        for i in range(15):
            a, b = 4 * math.sin(i * 0.55), 4 * math.sin((i + 1) * 0.55)
            line(-8 + i, a, -7 + i, b)
            line(-8 + i, -a, -7 + i, -b)
    elif key == "codon":
        for i in range(3):
            p.drawRoundedRect(QRectF(cx - 9 + i * 7, cy - 4, 5, 8), 1.2, 1.2)
    elif key == "pattern":
        p.drawEllipse(QPointF(cx - 2, cy - 2), 5.5, 5.5)
        line(2, 2, 8, 8)
    elif key == "similarity":
        p.drawEllipse(QPointF(cx - 3.5, cy), 5.5, 5.5)
        p.drawEllipse(QPointF(cx + 3.5, cy), 5.5, 5.5)
    elif key == "primer":
        line(0, -8, 0, 3)
        p.drawEllipse(QPointF(cx, cy + 5), 3.5, 3.5)
    elif key == "pdf":
        p.drawRoundedRect(QRectF(cx - 6, cy - 8, 12, 16), 2, 2)
        line(-3, -2, 3, -2)
        line(-3, 2, 3, 2)
    elif key == "panel":
        p.drawRoundedRect(QRectF(cx - 8, cy - 7, 16, 14), 3, 3)
        line(-3, -7, -3, 7)
    elif key == "bars":
        p.setBrush(QBrush(QColor(colour)))
        p.drawRoundedRect(QRectF(cx - 8, cy + 1, 4.5, 7), 1.2, 1.2)
        p.drawRoundedRect(QRectF(cx - 2.2, cy - 4, 4.5, 12), 1.2, 1.2)
        p.drawRoundedRect(QRectF(cx + 3.5, cy - 8, 4.5, 16), 1.2, 1.2)
    elif key == "drop":
        path = QPainterPath()
        path.moveTo(cx, cy - 9)
        path.cubicTo(cx + 9, cy + 1, cx + 7, cy + 9, cx, cy + 9)
        path.cubicTo(cx - 7, cy + 9, cx - 9, cy + 1, cx, cy - 9)
        p.setBrush(QBrush(QColor(colour)))
        p.drawPath(path)
    elif key == "leaf":
        path = QPainterPath()
        path.moveTo(cx - 8, cy + 8)
        path.cubicTo(cx - 9, cy - 4, cx + 1, cy - 9, cx + 9, cy - 9)
        path.cubicTo(cx + 9, cy, cx + 3, cy + 9, cx - 8, cy + 8)
        p.setBrush(QBrush(QColor(colour)))
        p.drawPath(path)
    elif key == "star":
        path = QPainterPath()
        for i in range(10):
            ang = -math.pi / 2 + i * math.pi / 5
            rad = 9 if i % 2 == 0 else 4
            point = QPointF(cx + rad * math.cos(ang), cy + rad * math.sin(ang))
            path.moveTo(point) if i == 0 else path.lineTo(point)
        path.closeSubpath()
        p.setBrush(QBrush(QColor(colour)))
        p.drawPath(path)
    elif key == "sparkle":
        path = QPainterPath()
        path.moveTo(cx, cy - 9)
        path.quadTo(cx, cy, cx + 9, cy)
        path.quadTo(cx, cy, cx, cy + 9)
        path.quadTo(cx, cy, cx - 9, cy)
        path.quadTo(cx, cy, cx, cy - 9)
        p.setBrush(QBrush(QColor(colour)))
        p.drawPath(path)
    elif key == "pie":
        p.drawEllipse(QPointF(cx, cy), 8, 8)
        p.setBrush(QBrush(QColor(colour)))
        p.drawPie(QRectF(cx - 8, cy - 8, 16, 16), 90 * 16, -100 * 16)
    elif key == "folder":
        p.setBrush(QBrush(QColor(colour)))
        p.drawRoundedRect(QRectF(cx - 8, cy - 7, 7, 4), 1.2, 1.2)
        p.drawRoundedRect(QRectF(cx - 8, cy - 4, 16, 11), 2, 2)
    elif key == "download":
        line(0, -8, 0, 3)
        line(-4, 0, 0, 4)
        line(4, 0, 0, 4)
        line(-7, 8, 7, 8)
        line(-7, 5, -7, 8)
        line(7, 5, 7, 8)
    elif key == "copy":
        p.drawRoundedRect(QRectF(cx - 4, cy - 8, 11, 11), 2, 2)
        p.drawRoundedRect(QRectF(cx - 8, cy - 4, 11, 11), 2, 2)


class NavButton(QPushButton):
    """Sidebar button: icon on the left, label when there is room (so it works as a collapsed rail too)."""

    def __init__(self, icon_key: str, label: str, parent=None):
        super().__init__(parent)
        self._icon_key = icon_key
        self._label = label
        self._active = False
        self.setToolTip(label)
        self.setFixedHeight(38)
        self.setMinimumWidth(40)
        self.setFocusPolicy(enum(Qt, "FocusPolicy", "NoFocus"))
        self.setCursor(enum(Qt, "CursorShape", "PointingHandCursor"))

    def set_active(self, on: bool):
        self._active = bool(on)
        self.update()

    def enterEvent(self, event):
        super().enterEvent(event)
        self.update()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(antialias_hint())
        h = self.height()
        hovered = self.underMouse() and self.isEnabled()
        if hovered and not self._active:
            p.setPen(no_pen())
            p.setBrush(QBrush(QColor(255, 255, 255, 30)))
            p.drawRoundedRect(QRectF(0, 0, self.width(), h), 10, 10)
        colour = "#FFFFFF" if (self._active or hovered) else "#C9DDF8"
        draw_nav_icon(p, self._icon_key, 21, h / 2.0, colour, 1.9)
        if self._label and self.width() >= 120:
            font = QFont(FONT_UI, 10)
            font.setBold(self._active)
            p.setFont(font)
            p.setPen(QColor(colour))
            mode = enum(Qt, "TextElideMode", "ElideRight")
            width = self.width() - 56
            text = p.fontMetrics().elidedText(self._label, mode, width)
            p.drawText(QRectF(46, 0, width, h), align_left(), text)


def badge_pixmap(key, fg, bg=None, size=36, scale=1.0):
    """An icon, optionally on a filled circle, as a crisp (2x) pixmap."""
    ratio = 2
    pix = QPixmap(size * ratio, size * ratio)
    pix.setDevicePixelRatio(ratio)
    pix.fill(QColor(0, 0, 0, 0))
    p = QPainter(pix)
    p.setRenderHint(antialias_hint())
    if bg:
        p.setPen(no_pen())
        p.setBrush(QBrush(QColor(bg)))
        p.drawEllipse(QRectF(0, 0, size, size))
    p.translate(size / 2.0, size / 2.0)
    p.scale(scale, scale)
    draw_nav_icon(p, key, 0, 0, fg, 1.8)
    p.end()
    return pix


def icon_for(key, colour, size=18):
    return QIcon(badge_pixmap(key, colour, None, size + 4, 1.0))


def icon_label(key, fg, bg=None, size=36, scale=1.0):
    label = QLabel()
    label.setPixmap(badge_pixmap(key, fg, bg, size, scale))
    label.setFixedSize(size, size)
    return label


class CardFrame(QFrame):
    """A rounded card with a soft shadow, an optional tone gradient and a faint corner decoration."""

    SHADOW = 6
    TONES = {
        "white": ("#FFFFFF", "#F3F8FF", "#2F6FE4"),
        "blue": ("#F1F7FF", "#D3E4FF", "#2F6FE4"),
        "teal": ("#EAF9FC", "#C9EEF4", "#119DB0"),
        "green": ("#EEFAF3", "#CBEDD9", "#1E9E66"),
        "purple": ("#F5F1FF", "#DED4FA", "#7C5CE0"),
    }

    def __init__(self, tone="white", deco=None, parent=None):
        super().__init__(parent)
        self._tone = tone if tone in self.TONES else "white"
        self._deco = deco
        self.setContentsMargins(self.SHADOW, self.SHADOW, self.SHADOW, self.SHADOW)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(antialias_hint())
        m = self.SHADOW
        rect = QRectF(m, m - 1, self.width() - 2 * m, self.height() - 2 * m)
        radius = 16.0

        p.setPen(no_pen())
        for grow, alpha in ((4.0, 7), (3.0, 9), (2.0, 12), (1.0, 16)):
            p.setBrush(QColor(20, 52, 120, alpha))
            p.drawRoundedRect(rect.adjusted(-grow, -grow + 2.5, grow, grow + 2.5), radius + grow, radius + grow)

        top, bottom, accent = self.TONES[self._tone]
        grad = QLinearGradient(rect.left(), rect.top(), rect.right(), rect.bottom())
        grad.setColorAt(0.0, QColor(top))
        grad.setColorAt(1.0, QColor(bottom))
        p.setBrush(QBrush(grad))
        p.setPen(QPen(QColor("#D5E3F7"), 1))
        p.drawRoundedRect(rect, radius, radius)

        if self._deco:
            clip = QPainterPath()
            clip.addRoundedRect(rect, radius, radius)
            p.save()
            p.setClipPath(clip)
            self._paint_deco(p, rect, QColor(accent))
            p.restore()

    def _paint_deco(self, p, rect, accent):
        w, h = rect.width(), rect.height()
        right, bottom = rect.right(), rect.bottom()
        p.setPen(no_pen())
        if self._deco == "wave":
            path = QPainterPath()
            path.moveTo(right - 0.55 * w, bottom)
            path.cubicTo(right - 0.35 * w, bottom - 0.28 * h, right - 0.12 * w, bottom - 0.3 * h, right, bottom - 0.62 * h)
            path.lineTo(right, bottom)
            path.closeSubpath()
            grad = QLinearGradient(right - 0.55 * w, bottom, right, bottom)
            grad.setColorAt(0.0, QColor(accent.red(), accent.green(), accent.blue(), 8))
            grad.setColorAt(1.0, QColor(accent.red(), accent.green(), accent.blue(), 120))
            p.setBrush(QBrush(grad))
            p.drawPath(path)
        elif self._deco == "helix":
            pen = QPen(QColor(accent.red(), accent.green(), accent.blue(), 120), 2.2)
            x0, y0 = right - 0.17 * w, rect.top() + 0.1 * h
            span = 0.82 * h
            for sign in (1, -1):
                prev = None
                for i in range(0, 41):
                    t = i / 40.0
                    pt = QPointF(x0 + sign * 12 * math.sin(t * 2.2 * math.pi), y0 + t * span)
                    if prev is not None:
                        p.setPen(pen)
                        p.drawLine(prev, pt)
                    prev = pt
            p.setPen(QPen(QColor(accent.red(), accent.green(), accent.blue(), 70), 1.6))
            for i in range(1, 12):
                t = i / 12.0
                dx = 12 * math.sin(t * 2.2 * math.pi)
                p.drawLine(QPointF(x0 - dx, y0 + t * span), QPointF(x0 + dx, y0 + t * span))
        elif self._deco == "leaf":
            path = QPainterPath()
            cx, cy = right - 0.14 * w, bottom - 0.3 * h
            path.moveTo(cx - 20, cy + 26)
            path.cubicTo(cx - 28, cy - 14, cx + 4, cy - 30, cx + 28, cy - 30)
            path.cubicTo(cx + 30, cy, cx + 10, cy + 30, cx - 20, cy + 26)
            p.setBrush(QBrush(QColor(accent.red(), accent.green(), accent.blue(), 70)))
            p.drawPath(path)
        elif self._deco == "question":
            p.setPen(QColor(accent.red(), accent.green(), accent.blue(), 85))
            font = QFont(FONT_UI, 40)
            font.setBold(True)
            p.setFont(font)
            p.drawText(QRectF(right - 0.3 * w, rect.top() + 0.2 * h, 0.26 * w, 0.7 * h), align_center(), "?")


class AppBackground(QWidget):
    """Soft blue gradient with faint helix watermarks behind the pages."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._top_mark = HelixWidget(self, vertical=False, pitch=280, rungs_per_turn=10, weight=1.5,
                                     max_amplitude=62, opacity=0.13, angle=-7, fade_ends=True)
        self._side_mark = HelixWidget(self, vertical=True, pitch=250, rungs_per_turn=10, weight=1.4,
                                      max_amplitude=60, opacity=0.12, angle=14, fade_ends=True)
        for mark in (self._top_mark, self._side_mark):
            mark.setAttribute(enum(Qt, "WidgetAttribute", "WA_TransparentForMouseEvents"))
            mark.lower()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        self._top_mark.setGeometry(int(w * 0.34), -6, min(620, int(w * 0.5)), 170)
        self._side_mark.setGeometry(max(0, w - 300), max(0, h - 420), 300, 420)
        self._top_mark.lower()
        self._side_mark.lower()

    def paintEvent(self, event):
        p = QPainter(self)
        grad = QLinearGradient(0, 0, self.width() * 0.4, self.height())
        grad.setColorAt(0.0, QColor(BG_TOP))
        grad.setColorAt(1.0, QColor(BG_BOTTOM))
        p.fillRect(self.rect(), QBrush(grad))


class SidebarFrame(QFrame):
    """The dark sidebar. Keeps its glowing background helix pinned to the bottom."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.bg_helix = None

    def attach_helix(self, helix):
        self.bg_helix = helix
        helix.setAttribute(enum(Qt, "WidgetAttribute", "WA_TransparentForMouseEvents"))
        self._place()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._place()

    def _place(self):
        if self.bg_helix is not None:
            height = int(min(300, self.height() * 0.4))
            self.bg_helix.setGeometry(0, self.height() - height - 40, self.width(), height)


class PillFrame(QFrame):
    """A fully rounded background pill, painted directly so the ends are always round."""

    def __init__(self, fill="#1B3A72", border=None, parent=None):
        super().__init__(parent)
        self._fill = fill
        self._border = border

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(antialias_hint())
        rect = QRectF(0.5, 0.5, self.width() - 1.0, self.height() - 1.0)
        p.setPen(QPen(QColor(self._border), 1) if self._border else no_pen())
        p.setBrush(QBrush(QColor(self._fill)))
        p.drawRoundedRect(rect, rect.height() / 2.0, rect.height() / 2.0)