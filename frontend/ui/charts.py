import math

from frontend.ui.qt_compat import (
    QWidget,
    QPainter,
    QColor,
    QPen,
    QBrush,
    QFont,
    QRectF,
    QPointF,
    QPainterPath,
    QLinearGradient,
    antialias_hint,
    no_pen,
    dash_pen_style,
    align_center,
    align_left,
    align_right,
)
from frontend.ui.qt_extra import get_qt, enum
from frontend.ui.theme import (
    BASE_FILL,
    BASE_NAMES,
    BORDER,
    FAINT,
    FONT_UI,
    INK,
    MUTED,
    NAVY,
)

QTimer = get_qt("QTimer")
Qt = get_qt("Qt")

BASE_ORDER = ["A", "T", "G", "C", "N"]
GRID = "#E5EAF1"


def make_font(size: float, bold: bool = False) -> QFont:
    font = QFont(FONT_UI, int(size))
    if size != int(size):
        font.setPointSizeF(size)
    font.setBold(bold)
    return font


class BaseCompositionChart(QWidget):
    """Pie chart of base composition with a legend of counts and percentages."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(260)
        self.counts = {b: 0 for b in BASE_ORDER}

    def set_counts(self, counts: dict):
        self.counts = {b: int(counts.get(b, 0)) for b in BASE_ORDER}
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(antialias_hint())

        w, h = self.width(), self.height()
        total = sum(self.counts.values())
        pad = 8
        size = max(90, min(h - 2 * pad, int(w * 0.42), 280))
        rect = QRectF(pad + 6, (h - size) / 2.0, size, size)

        if total == 0:
            painter.setPen(QPen(QColor(GRID), 2))
            painter.setBrush(QBrush(QColor("#F4F7FB")))
            painter.drawEllipse(rect)
            painter.setPen(QColor(FAINT))
            painter.setFont(make_font(10))
            painter.drawText(rect, align_center(), "No sequence loaded")
            return

        # ---- pie ----
        start = 90 * 16.0
        centre = rect.center()
        radius = size / 2.0
        slices = []
        for base in BASE_ORDER:
            val = self.counts[base]
            if val <= 0:
                continue
            span = (val / total) * 360.0 * 16.0
            painter.setPen(QPen(QColor("#FFFFFF"), 2))
            painter.setBrush(QBrush(QColor(BASE_FILL[base])))
            painter.drawPie(rect, int(round(start)), int(round(-span)))
            slices.append((base, start, span, val / total * 100.0))
            start -= span

        painter.setFont(make_font(9, True))
        for base, begin, span, pct in slices:
            if pct < 6.0:
                continue
            mid = math.radians((begin - span / 2.0) / 16.0)
            tx = centre.x() + radius * 0.64 * math.cos(mid)
            ty = centre.y() - radius * 0.64 * math.sin(mid)
            painter.setPen(QColor(INK) if base == "G" else QColor("#FFFFFF"))
            painter.drawText(QRectF(tx - 32, ty - 10, 64, 20), align_center(), f"{pct:.1f}%")

        # ---- legend ----
        lx = rect.right() + 36
        lw = max(170.0, w - lx - 16)
        row_h = max(38.0, min(54.0, (h - 2 * pad - 34) / 5.0))
        block_h = 34 + row_h * 5
        top = max(pad, (h - block_h) / 2.0)

        painter.setPen(QColor(INK))
        painter.setFont(make_font(11, True))
        painter.drawText(QRectF(lx, top, lw, 20), align_left(), f"{total:,} bases")
        painter.setPen(QColor(FAINT))
        painter.setFont(make_font(8))
        painter.drawText(QRectF(lx, top, lw, 20), align_right(), "share of all bases")

        for idx, base in enumerate(BASE_ORDER):
            y = top + 34 + idx * row_h
            val = self.counts[base]
            pct = val / total * 100.0

            painter.setPen(no_pen())
            painter.setBrush(QBrush(QColor(BASE_FILL[base])))
            painter.drawRoundedRect(QRectF(lx, y + 5, 10, 10), 3, 3)

            painter.setPen(QColor(INK))
            painter.setFont(make_font(9.5, True))
            painter.drawText(QRectF(lx + 18, y, lw - 18, 20), align_left(), BASE_NAMES[base])
            painter.setPen(QColor(MUTED))
            painter.setFont(make_font(9.5))
            painter.drawText(QRectF(lx, y, lw, 20), align_right(), f"{val:,}  ({pct:.1f}%)")

            track = QRectF(lx, y + 24, lw, 6)
            painter.setPen(no_pen())
            painter.setBrush(QBrush(QColor("#EDF1F6")))
            painter.drawRoundedRect(track, 3, 3)
            if val > 0:
                painter.setBrush(QBrush(QColor(BASE_FILL[base])))
                painter.drawRoundedRect(QRectF(lx, y + 24, max(6.0, lw * val / total), 6), 3, 3)


class GcLineChart(QWidget):
    """GC percentage across sliding windows, with a dashed mean line."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(260)
        self.windows = []

    def set_windows(self, windows: list):
        self.windows = windows or []
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(antialias_hint())

        w, h = self.width(), self.height()
        left_pad, right_pad, top_pad, bot_pad = 48, 22, 28, 34
        plot_w = max(100, w - left_pad - right_pad)
        plot_h = max(80, h - top_pad - bot_pad)

        painter.setFont(make_font(8))
        for pct in (0, 25, 50, 75, 100):
            y = top_pad + plot_h - (pct / 100.0) * plot_h
            pen = QPen(QColor("#C9D3E0") if pct == 50 else QColor(GRID), 1)
            if pct == 50:
                pen.setStyle(dash_pen_style())
            painter.setPen(pen)
            painter.drawLine(QPointF(left_pad, y), QPointF(left_pad + plot_w, y))
            painter.setPen(QColor(FAINT))
            painter.drawText(QRectF(4, y - 9, left_pad - 10, 18), align_right(), f"{pct}%")

        if not self.windows:
            painter.setPen(QColor(FAINT))
            painter.setFont(make_font(10))
            painter.drawText(
                QRectF(left_pad, top_pad, plot_w, plot_h),
                align_center(),
                "Set a window size and step above, then run the analysis.",
            )
            return

        n = len(self.windows)
        points = []
        for idx, item in enumerate(self.windows):
            x = left_pad + (plot_w / 2.0 if n == 1 else (idx / (n - 1)) * plot_w)
            y = top_pad + plot_h - (item["gc_pct"] / 100.0) * plot_h
            points.append(QPointF(x, y))

        fill_path = QPainterPath()
        fill_path.moveTo(points[0].x(), top_pad + plot_h)
        for pt in points:
            fill_path.lineTo(pt)
        fill_path.lineTo(points[-1].x(), top_pad + plot_h)
        fill_path.closeSubpath()
        grad = QLinearGradient(0, top_pad, 0, top_pad + plot_h)
        grad.setColorAt(0.0, QColor(59, 130, 246, 70))
        grad.setColorAt(1.0, QColor(59, 130, 246, 4))
        painter.setPen(no_pen())
        painter.setBrush(QBrush(grad))
        painter.drawPath(fill_path)

        line_path = QPainterPath()
        line_path.moveTo(points[0])
        for pt in points[1:]:
            line_path.lineTo(pt)
        painter.setPen(QPen(QColor("#2F6FE4"), 2.4))
        painter.setBrush(QBrush())
        painter.drawPath(line_path)

        mean = sum(item["gc_pct"] for item in self.windows) / n
        mean_y = top_pad + plot_h - (mean / 100.0) * plot_h
        mean_pen = QPen(QColor("#A76A00"), 1.4)
        mean_pen.setStyle(dash_pen_style())
        painter.setPen(mean_pen)
        painter.drawLine(QPointF(left_pad, mean_y), QPointF(left_pad + plot_w, mean_y))
        painter.setFont(make_font(8, True))
        painter.drawText(QRectF(left_pad, 2, plot_w, 16), align_right(), f"- - mean GC {mean:.1f}%")

        if n <= 60:
            painter.setPen(QPen(QColor("#FFFFFF"), 1.5))
            painter.setBrush(QBrush(QColor("#2FA66A")))
            for pt in points:
                painter.drawEllipse(pt, 3.8, 3.8)

        painter.setPen(QColor(FAINT))
        painter.setFont(make_font(8))
        painter.drawText(
            QRectF(left_pad, top_pad + plot_h + 8, 160, 18),
            align_left(),
            f"Window 1 (bp {self.windows[0]['start']})",
        )
        painter.drawText(
            QRectF(left_pad + plot_w - 180, top_pad + plot_h + 8, 180, 18),
            align_right(),
            f"Window {n} (bp {self.windows[-1]['end']})",
        )


class HelixWidget(QWidget):
    """A simple double helix whose rungs are coloured A-T / G-C base pairs."""

    _PAIRS = ["AT", "GC", "TA", "CG", "AT", "GC", "GC", "TA", "CG", "AT", "TA", "GC", "CG", "AT", "TA", "CG"]
    _STRAND_FRONT = ("#14274E", "#5B7DB1")
    _STRAND_BACK = ((20, 39, 78, 110), (91, 125, 177, 110))

    def __init__(self, parent=None, vertical=True, animated=False, pitch=170.0,
                 rungs_per_turn=9, weight=1.0, max_amplitude=110.0):
        super().__init__(parent)
        self._vertical = vertical
        self._animated = animated
        self._pitch = float(pitch)
        self._rungs_per_turn = int(rungs_per_turn)
        self._weight = float(weight)
        self._max_amp = float(max_amplitude)
        self._phase = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(40)
        self._timer.timeout.connect(self._tick)

    def showEvent(self, event):
        super().showEvent(event)
        if self._animated:
            self._timer.start()

    def hideEvent(self, event):
        super().hideEvent(event)
        self._timer.stop()

    def _tick(self):
        self._phase = (self._phase + 0.045) % (2 * math.pi)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(antialias_hint())

        w, h = self.width(), self.height()
        length, span = (h, w) if self._vertical else (w, h)
        margin = 10 if self._weight < 0.8 else 18
        amp = max(5.0, min(span / 2.0 - margin, self._max_amp))
        centre = span / 2.0
        wt = self._weight
        round_cap = enum(Qt, "PenCapStyle", "RoundCap")

        def pt(s, c):
            return QPointF(c, s) if self._vertical else QPointF(s, c)

        def phase_at(s):
            return self._phase + (s / self._pitch) * 2 * math.pi

        # backbone segments, split into those behind and in front of the rungs
        back, front = [], []
        step = 4.0
        s = margin
        while s < length - margin:
            s2 = min(s + step, length - margin)
            mid = phase_at((s + s2) / 2.0)
            for strand, sign in ((0, 1.0), (1, -1.0)):
                a = pt(s, centre + sign * amp * math.sin(phase_at(s)))
                b = pt(s2, centre + sign * amp * math.sin(phase_at(s2)))
                is_front = (math.cos(mid) > 0) if strand == 0 else (math.cos(mid) < 0)
                (front if is_front else back).append((a, b, strand))
            s = s2

        for a, b, strand in back:
            pen = QPen(QColor(*self._STRAND_BACK[strand]), 2.4 * wt)
            pen.setCapStyle(enum(Qt, "PenCapStyle", "FlatCap"))
            painter.setPen(pen)
            painter.drawLine(a, b)

        # base-pair rungs
        spacing = self._pitch / self._rungs_per_turn
        i = 0
        s = margin + spacing / 2.0
        while s < length - margin:
            ph = phase_at(s)
            c1 = centre + amp * math.sin(ph)
            c2 = centre - amp * math.sin(ph)
            if abs(c1 - c2) > 4:
                b1, b2 = self._PAIRS[i % len(self._PAIRS)]
                p1, p2 = pt(s, c1), pt(s, c2)
                mid_pt = pt(s, (c1 + c2) / 2.0)
                for start, end, base in ((p1, mid_pt, b1), (mid_pt, p2, b2)):
                    pen = QPen(QColor(BASE_FILL[base]), 4.2 * wt)
                    pen.setCapStyle(round_cap)
                    painter.setPen(pen)
                    painter.drawLine(start, end)
            s += spacing
            i += 1

        for a, b, strand in front:
            pen = QPen(QColor(self._STRAND_FRONT[strand]), 3.8 * wt)
            pen.setCapStyle(round_cap)
            painter.setPen(pen)
            painter.drawLine(a, b)
