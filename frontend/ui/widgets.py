"""Small reusable widgets: elided label and a base-coloured sequence viewer."""
import re

from frontend.ui.qt_compat import QLabel, QPlainTextEdit, QColor
from frontend.ui.qt_extra import get_qt, enum
from frontend.ui.theme import BASE_TEXT

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
    """Read-only monospace viewer. Bases A/T/U/G/C/N are coloured to match the charts."""

    def __init__(self, highlight: bool = True, parent=None):
        super().__init__(parent)
        self.setProperty("class", "SeqBox")
        self.setReadOnly(True)
        self.setMinimumHeight(90)
        self.setLineWrapMode(enum(QPlainTextEdit, "LineWrapMode", "NoWrap"))
        self._highlighter = BaseHighlighter(self.document()) if highlight else None
