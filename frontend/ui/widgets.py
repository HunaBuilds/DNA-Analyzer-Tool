"""Small reusable widgets: elided label and a base-coloured sequence viewer."""
import math
import re

from frontend.ui.qt_compat import (
    QLabel, QPlainTextEdit, QPushButton, QColor, QPainter, QPen, QBrush, QFont, QRectF, QPointF,
    antialias_hint, no_pen, align_left,
)
from frontend.ui.qt_extra import get_qt, enum
from frontend.ui.theme import BASE_TEXT, FONT_UI, INK, MUTED, NAVY

QSize = get_qt("QSize")
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


def draw_nav_icon(p, key, cx, cy, colour):
    """Tiny line icons for the sidebar, drawn with the painter so they stay crisp and recolourable."""
    pen = QPen(QColor(colour), 1.7)
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
            p.setBrush(QBrush(QColor("#F1F5FA")))
            p.drawRoundedRect(QRectF(0, 0, self.width(), h), 8, 8)
        colour = NAVY if self._active else (INK if hovered else MUTED)
        draw_nav_icon(p, self._icon_key, 20, h / 2.0, colour)
        if self._label and self.width() >= 120:
            font = QFont(FONT_UI, 10)
            font.setBold(self._active)
            p.setFont(font)
            p.setPen(QColor(colour))
            mode = enum(Qt, "TextElideMode", "ElideRight")
            width = self.width() - 54
            text = p.fontMetrics().elidedText(self._label, mode, width)
            p.drawText(QRectF(44, 0, width, h), align_left(), text)