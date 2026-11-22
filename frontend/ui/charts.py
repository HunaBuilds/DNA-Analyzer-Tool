import math
import random

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
from frontend.ui.qt_extra import get_qt, enum, make_animation, event_pos
from frontend.ui.theme import (
    BASE_FILL,
    BASE_NAMES,
    FAINT,
    FONT_UI,
    INK,
    MUTED,
    NAVY,
    TINT,
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


def draw_bubble(painter, lines, x, y, bounds_w, bounds_h):
    """A small dark tooltip bubble near (x, y), kept inside the widget."""
    painter.setFont(make_font(9, True))
    fm = painter.fontMetrics()
    text_w = max(fm.horizontalAdvance(t) for t in lines)
    line_h = fm.height()
    bw, bh = text_w + 20, line_h * len(lines) + 14
    bx = x + 14
    if bx + bw > bounds_w - 6:
        bx = x - 14 - bw
    bx = max(6.0, bx)
    by = min(max(6.0, y + 14), bounds_h - bh - 6)
    painter.setPen(no_pen())
    painter.setBrush(QBrush(QColor(NAVY)))
    painter.drawRoundedRect(QRectF(bx, by, bw, bh), 8, 8)
    painter.setPen(QColor("#FFFFFF"))
    for i, text in enumerate(lines):
        painter.drawText(QRectF(bx + 10, by + 7 + i * line_h, text_w + 4, line_h), align_left(), text)


class BaseCompositionChart(QWidget):
    """Pie chart that sweeps in, lifts a slice on hover, and has a matching legend."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(260)
        self.setMouseTracking(True)
        self.counts = {b: 0 for b in BASE_ORDER}
        self._progress = 1.0
        self._hover = None
        self._mouse = None
        self._pie = None
        self._legend_rects = {}
        self._anim = make_animation(self, 950, 0.0, 1.0, self._on_progress)

    def _on_progress(self, value):
        self._progress = float(value)
        self.update()

    def set_counts(self, counts: dict):
        self.counts = {b: int(counts.get(b, 0)) for b in BASE_ORDER}
        self._hover = None
        self._anim.stop()
        if sum(self.counts.values()) > 0:
            self._progress = 0.0
            self._anim.start()
        else:
            self._progress = 1.0
        self.update()

    # ---- interaction
    def _base_at(self, x, y):
        for base, rect in self._legend_rects.items():
            if rect.contains(QPointF(x, y)):
                return base, False
        total = sum(self.counts.values())
        if self._pie and total > 0:
            cx, cy, radius = self._pie
            dx, dy = x - cx, y - cy
            if math.hypot(dx, dy) <= radius:
                angle = math.degrees(math.atan2(-dy, dx)) % 360.0
                clockwise_from_top = (90.0 - angle) % 360.0
                running = 0.0
                for base in BASE_ORDER:
                    running += self.counts[base] / total * 360.0
                    if self.counts[base] > 0 and clockwise_from_top <= running:
                        return base, True
        return None, False

    def mouseMoveEvent(self, event):
        x, y = event_pos(event)
        base, _ = self._base_at(x, y)
        self._mouse = (x, y)
        self._hover = base
        self.update()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self._hover = None
        self._mouse = None
        self.update()

    # ---- painting
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(antialias_hint())

        w, h = self.width(), self.height()
        total = sum(self.counts.values())
        pad = 8
        size = max(90, min(h - 2 * pad - 18, int(w * 0.42), 270))
        rect = QRectF(pad + 14, (h - size) / 2.0, size, size)
        self._pie = (rect.center().x(), rect.center().y(), size / 2.0)
        self._legend_rects = {}

        if total == 0:
            painter.setPen(QPen(QColor(GRID), 2))
            painter.setBrush(QBrush(QColor("#F4F7FB")))
            painter.drawEllipse(rect)
            painter.setPen(QColor(FAINT))
            painter.setFont(make_font(10))
            painter.drawText(rect, align_center(), "No sequence loaded")
            return

        prog = self._progress
        centre = rect.center()
        radius = size / 2.0

        # ---- pie (the hovered slice is drawn last so its lift sits on top)
        start = 90 * 16.0
        slices = []
        for base in BASE_ORDER:
            val = self.counts[base]
            if val <= 0:
                continue
            full = (val / total) * 360.0 * 16.0
            slices.append((base, start, full * prog, val / total * 100.0))
            start -= full * prog
        ordered = [s for s in slices if s[0] != self._hover] + [s for s in slices if s[0] == self._hover]
        for base, begin, span, pct in ordered:
            slice_rect = rect
            if base == self._hover:
                mid = math.radians((begin - span / 2.0) / 16.0)
                slice_rect = rect.translated(9 * math.cos(mid), -9 * math.sin(mid))
            painter.setPen(QPen(QColor("#FFFFFF"), 2))
            painter.setBrush(QBrush(QColor(BASE_FILL[base])))
            painter.drawPie(slice_rect, int(round(begin)), int(round(-span)))

        if prog > 0.97:
            painter.setFont(make_font(9, True))
            for base, begin, span, pct in slices:
                if pct < 6.0:
                    continue
                mid = math.radians((begin - span / 2.0) / 16.0)
                lift = 9 if base == self._hover else 0
                tx = centre.x() + (radius * 0.64 + lift) * math.cos(mid)
                ty = centre.y() - (radius * 0.64 + lift) * math.sin(mid)
                painter.setPen(QColor(INK) if base == "G" else QColor("#FFFFFF"))
                painter.drawText(QRectF(tx - 32, ty - 10, 64, 20), align_center(), f"{pct:.1f}%")

        # ---- legend
        lx = rect.right() + 40
        lw = max(170.0, w - lx - 18)
        row_h = max(38.0, min(54.0, (h - 2 * pad - 34) / 5.0))
        top = max(pad, (h - (34 + row_h * 5)) / 2.0)

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
            row_rect = QRectF(lx - 8, y - 4, lw + 16, 36)
            self._legend_rects[base] = row_rect

            if base == self._hover:
                painter.setPen(no_pen())
                painter.setBrush(QBrush(QColor(TINT)))
                painter.drawRoundedRect(row_rect, 8, 8)

            painter.setPen(no_pen())
            painter.setBrush(QBrush(QColor(BASE_FILL[base])))
            painter.drawRoundedRect(QRectF(lx, y + 5, 10, 10), 3, 3)
            painter.setPen(QColor(INK))
            painter.setFont(make_font(9.5, True))
            painter.drawText(QRectF(lx + 18, y, lw - 18, 20), align_left(), BASE_NAMES[base])
            painter.setPen(QColor(MUTED))
            painter.setFont(make_font(9.5))
            painter.drawText(QRectF(lx, y, lw, 20), align_right(), f"{val:,}  ({pct:.1f}%)")

            painter.setPen(no_pen())
            painter.setBrush(QBrush(QColor("#E6EBF2" if base == self._hover else "#EDF1F6")))
            painter.drawRoundedRect(QRectF(lx, y + 24, lw, 6), 3, 3)
            if val > 0:
                painter.setBrush(QBrush(QColor(BASE_FILL[base])))
                painter.drawRoundedRect(QRectF(lx, y + 24, max(6.0, lw * val / total * prog), 6), 3, 3)

        if self._hover and self._mouse and self._mouse[0] < rect.right() + 14:
            val = self.counts[self._hover]
            draw_bubble(
                painter,
                [BASE_NAMES[self._hover], f"{val:,} bases  |  {val / total * 100.0:.1f}%"],
                self._mouse[0], self._mouse[1], w, h,
            )


class GcLineChart(QWidget):
    """GC percentage across sliding windows: draws in left to right, hover shows the exact window."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(260)
        self.setMouseTracking(True)
        self.windows = []
        self._progress = 1.0
        self._hover_idx = None
        self._plot = (48, 28, 100, 80)
        self._anim = make_animation(self, 1000, 0.0, 1.0, self._on_progress)

    def _on_progress(self, value):
        self._progress = float(value)
        self.update()

    def set_windows(self, windows: list):
        self.windows = windows or []
        self._hover_idx = None
        self._anim.stop()
        if self.windows:
            self._progress = 0.0
            self._anim.start()
        else:
            self._progress = 1.0
        self.update()

    def mouseMoveEvent(self, event):
        if not self.windows:
            return
        x, y = event_pos(event)
        left, top, plot_w, plot_h = self._plot
        n = len(self.windows)
        if left - 8 <= x <= left + plot_w + 8 and top - 8 <= y <= top + plot_h + 8:
            idx = 0 if n == 1 else int(round((x - left) / plot_w * (n - 1)))
            self._hover_idx = max(0, min(n - 1, idx))
        else:
            self._hover_idx = None
        self.update()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self._hover_idx = None
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(antialias_hint())

        w, h = self.width(), self.height()
        left_pad, right_pad, top_pad, bot_pad = 48, 22, 28, 34
        plot_w = max(100, w - left_pad - right_pad)
        plot_h = max(80, h - top_pad - bot_pad)
        self._plot = (left_pad, top_pad, plot_w, plot_h)

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

        mean = sum(item["gc_pct"] for item in self.windows) / n
        mean_y = top_pad + plot_h - (mean / 100.0) * plot_h

        painter.save()
        painter.setClipRect(QRectF(left_pad - 8, 0, plot_w * self._progress + 16, h))

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

        mean_pen = QPen(QColor("#A76A00"), 1.4)
        mean_pen.setStyle(dash_pen_style())
        painter.setPen(mean_pen)
        painter.drawLine(QPointF(left_pad, mean_y), QPointF(left_pad + plot_w, mean_y))

        if n <= 60:
            painter.setPen(QPen(QColor("#FFFFFF"), 1.5))
            painter.setBrush(QBrush(QColor("#2FA66A")))
            for pt in points:
                painter.drawEllipse(pt, 3.8, 3.8)
        painter.restore()

        painter.setPen(QColor("#A76A00"))
        painter.setFont(make_font(8, True))
        painter.drawText(QRectF(left_pad, 2, plot_w, 16), align_right(), f"- - mean GC {mean:.1f}%")

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

        if self._hover_idx is not None and self._progress >= 1.0:
            item = self.windows[self._hover_idx]
            pt = points[self._hover_idx]
            guide = QPen(QColor("#9FB0C6"), 1)
            guide.setStyle(dash_pen_style())
            painter.setPen(guide)
            painter.drawLine(QPointF(pt.x(), top_pad), QPointF(pt.x(), top_pad + plot_h))
            painter.setPen(QPen(QColor("#FFFFFF"), 2))
            painter.setBrush(QBrush(QColor("#2F6FE4")))
            painter.drawEllipse(pt, 6, 6)
            draw_bubble(
                painter,
                [
                    f"Window {item['index']}  (bp {item['start']}-{item['end']})",
                    f"GC {item['gc_pct']:.2f}%   AT {item['at_pct']:.2f}%",
                ],
                pt.x(), pt.y(), w, h,
            )


class HelixWidget(QWidget):
    """Double helix with A-T / G-C rungs. Optional: spin speed, drifting bases, mouse scrubbing."""

    _PAIRS = ["AT", "GC", "TA", "CG", "AT", "GC", "GC", "TA", "CG", "AT", "TA", "GC", "CG", "AT", "TA", "CG"]
    _STRAND_FRONT = ("#14274E", "#5B7DB1")
    _STRAND_BACK = ((20, 39, 78, 110), (91, 125, 177, 110))

    def __init__(self, parent=None, vertical=True, animated=False, pitch=170.0,
                 rungs_per_turn=9, weight=1.0, max_amplitude=110.0,
                 particles=False, interactive=False):
        super().__init__(parent)
        self._vertical = vertical
        self._animated = animated
        self._pitch = float(pitch)
        self._rungs_per_turn = int(rungs_per_turn)
        self._weight = float(weight)
        self._max_amp = float(max_amplitude)
        self._phase = 0.0
        self._pulse = 0.0
        self._base_speed = 1.0
        self._boost = 0.0
        self._speed = 1.0
        self._interactive = interactive
        self._dragging = False
        self._drag_x = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._tick)

        self._particles = []
        if particles:
            rng = random.Random(7)
            for _ in range(24):
                self._particles.append({
                    "x": rng.random(), "y": rng.random(), "v": 0.004 + rng.random() * 0.008,
                    "b": rng.choice("ATGC"), "s": 9 + rng.random() * 9, "a": 45 + int(rng.random() * 60),
                })
        if interactive:
            self.setMouseTracking(True)
            self.setCursor(enum(Qt, "CursorShape", "OpenHandCursor"))

    # ---- control
    def set_speed(self, speed: float):
        self._base_speed = float(speed)

    def showEvent(self, event):
        super().showEvent(event)
        if self._animated:
            self._timer.start()

    def hideEvent(self, event):
        super().hideEvent(event)
        self._timer.stop()

    def _tick(self):
        target = self._base_speed + self._boost
        self._speed += (target - self._speed) * 0.12
        self._phase = (self._phase + 0.04 * self._speed) % (2 * math.pi)
        self._pulse = (self._pulse + 0.006 * max(1.0, self._speed)) % 1.0
        for p in self._particles:
            p["y"] -= p["v"] * (0.5 + 0.5 * self._speed)
            if p["y"] < -0.05:
                p["y"] = 1.05
        self.update()

    # ---- mouse
    def enterEvent(self, event):
        super().enterEvent(event)
        if self._interactive:
            self._boost = 1.4

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self._boost = 0.0

    def mousePressEvent(self, event):
        if self._interactive:
            self._dragging = True
            self._drag_x = event_pos(event)[0]
            self.setCursor(enum(Qt, "CursorShape", "ClosedHandCursor"))

    def mouseMoveEvent(self, event):
        if self._dragging:
            x = event_pos(event)[0]
            self._phase = (self._phase + (x - self._drag_x) * 0.03) % (2 * math.pi)
            self._drag_x = x
            self.update()

    def mouseReleaseEvent(self, event):
        if self._dragging:
            self._dragging = False
            self.setCursor(enum(Qt, "CursorShape", "OpenHandCursor"))

    # ---- painting
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(antialias_hint())

        w, h = self.width(), self.height()

        for p in self._particles:
            colour = QColor(BASE_FILL[p["b"]])
            colour.setAlpha(p["a"])
            painter.setPen(colour)
            painter.setFont(make_font(p["s"], True))
            painter.drawText(QRectF(p["x"] * w - 12, p["y"] * h - 12, 24, 24), align_center(), p["b"])

        length, span = (h, w) if self._vertical else (w, h)
        margin = 10 if self._weight < 0.8 else 18
        amp = max(5.0, min(span / 2.0 - margin, self._max_amp))
        centre = span / 2.0
        wt = self._weight
        round_cap = enum(Qt, "PenCapStyle", "RoundCap")
        flat_cap = enum(Qt, "PenCapStyle", "FlatCap")

        def pt(s, c):
            return QPointF(c, s) if self._vertical else QPointF(s, c)

        def phase_at(s):
            return self._phase + (s / self._pitch) * 2 * math.pi

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
            pen.setCapStyle(flat_cap)
            painter.setPen(pen)
            painter.drawLine(a, b)

        spacing = self._pitch / self._rungs_per_turn
        pulse_at = self._pulse * length
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
                glow = 1.0
                if self._animated:
                    dist = abs(s - pulse_at)
                    if dist < 46:
                        glow = 1.0 + 0.9 * (1.0 - dist / 46.0)
                for start, end, base in ((p1, mid_pt, b1), (mid_pt, p2, b2)):
                    pen = QPen(QColor(BASE_FILL[base]), 4.2 * wt * glow)
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
