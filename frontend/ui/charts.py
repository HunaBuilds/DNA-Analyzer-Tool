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


class BaseCompositionChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(250)
        self.counts = {"A": 0, "T": 0, "G": 0, "C": 0, "N": 0}
        self.colors = {
            "A": QColor("#38bdf8"),
            "T": QColor("#f472b6"),
            "G": QColor("#34d399"),
            "C": QColor("#fbbf24"),
            "N": QColor("#94a3b8"),
        }
        self.labels = {
            "A": "Adenine (A)",
            "T": "Thymine (T)",
            "G": "Guanine (G)",
            "C": "Cytosine (C)",
            "N": "Ambiguous (N)",
        }

    def set_counts(self, counts: dict):
        self.counts = {
            "A": int(counts.get("A", 0)),
            "T": int(counts.get("T", 0)),
            "G": int(counts.get("G", 0)),
            "C": int(counts.get("C", 0)),
            "N": int(counts.get("N", 0)),
        }
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(antialias_hint())

        w = self.width()
        h = self.height()
        total = sum(self.counts.values())

        donut_size = min(h - 40, int(w * 0.36), 190)
        donut_x = 24
        donut_y = (h - donut_size) // 2
        donut_rect = QRectF(donut_x, donut_y, donut_size, donut_size)

        if total == 0:
            painter.setPen(QPen(QColor("#334155"), 14))
            painter.drawEllipse(donut_rect.adjusted(12, 12, -12, -12))
            painter.setPen(QColor("#94a3b8"))
            painter.setFont(QFont("Segoe UI", 10))
            painter.drawText(donut_rect, align_center(), "No Sequence")
            return

        start_angle = 90 * 16
        ring_rect = donut_rect.adjusted(14, 14, -14, -14)
        for base in ["A", "T", "G", "C", "N"]:
            val = self.counts[base]
            if val <= 0:
                continue
            span = int(round((val / total) * 360 * 16))
            pen = QPen(self.colors[base], 18)
            painter.setPen(pen)
            painter.drawArc(ring_rect, start_angle, -span)
            start_angle -= span

        painter.setPen(QColor("#f8fafc"))
        painter.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold if hasattr(QFont, "Weight") else 75))
        painter.drawText(ring_rect.adjusted(0, -10, 0, -10), align_center(), f"{total:,}")
        painter.setPen(QColor("#94a3b8"))
        painter.setFont(QFont("Segoe UI", 8))
        painter.drawText(ring_rect.adjusted(0, 14, 0, 14), align_center(), "Total Bases")

        bar_area_x = donut_x + donut_size + 36
        bar_area_w = max(140, w - bar_area_x - 24)
        row_h = (h - 32) / 5.0

        for idx, base in enumerate(["A", "T", "G", "C", "N"]):
            y_top = 16 + idx * row_h
            val = self.counts[base]
            pct = (val / total) * 100.0 if total > 0 else 0.0

            painter.setPen(QColor("#e2e8f0"))
            painter.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold if hasattr(QFont, "Weight") else 63))
            painter.drawText(QRectF(bar_area_x, y_top, 115, 20), align_left(), self.labels[base])

            painter.setPen(QColor("#94a3b8"))
            painter.setFont(QFont("Segoe UI", 9))
            painter.drawText(
                QRectF(bar_area_x + bar_area_w - 110, y_top, 110, 20),
                align_right(),
                f"{val:,} ({pct:.1f}%)",
            )

            track_rect = QRectF(bar_area_x, y_top + 22, bar_area_w, 8)
            painter.setPen(no_pen())
            painter.setBrush(QBrush(QColor("#1e293b")))
            painter.drawRoundedRect(track_rect, 4, 4)

            fill_w = max(0.0, bar_area_w * (val / total))
            if fill_w > 0:
                fill_rect = QRectF(bar_area_x, y_top + 22, fill_w, 8)
                painter.setBrush(QBrush(self.colors[base]))
                painter.drawRoundedRect(fill_rect, 4, 4)


class GcLineChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(250)
        self.windows = []

    def set_windows(self, windows: list):
        self.windows = windows or []
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(antialias_hint())

        w = self.width()
        h = self.height()
        left_pad = 48
        right_pad = 22
        top_pad = 20
        bot_pad = 34

        plot_w = max(100, w - left_pad - right_pad)
        plot_h = max(80, h - top_pad - bot_pad)

        painter.setFont(QFont("Segoe UI", 8))
        for pct in [0, 25, 50, 75, 100]:
            y = top_pad + plot_h - (pct / 100.0) * plot_h
            pen_color = QColor("#475569") if pct == 50 else QColor("#1e293b")
            pen = QPen(pen_color, 1)
            if pct == 50:
                pen.setStyle(dash_pen_style())
            painter.setPen(pen)
            painter.drawLine(QPointF(left_pad, y), QPointF(left_pad + plot_w, y))

            painter.setPen(QColor("#94a3b8"))
            painter.drawText(QRectF(4, y - 9, left_pad - 10, 18), align_right(), f"{pct}%")

        if not self.windows:
            painter.setPen(QColor("#64748b"))
            painter.setFont(QFont("Segoe UI", 10))
            painter.drawText(
                QRectF(left_pad, top_pad, plot_w, plot_h),
                align_center(),
                "Configure Window Size and Step Size above, then click Run GC Window Analysis.",
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
        grad.setColorAt(0.0, QColor(56, 189, 248, 95))
        grad.setColorAt(1.0, QColor(56, 189, 248, 5))
        painter.setPen(no_pen())
        painter.setBrush(QBrush(grad))
        painter.drawPath(fill_path)

        line_path = QPainterPath()
        line_path.moveTo(points[0])
        for pt in points[1:]:
            line_path.lineTo(pt)
        painter.setPen(QPen(QColor("#38bdf8"), 2.4))
        painter.setBrush(QBrush())
        painter.drawPath(line_path)

        if n <= 60:
            painter.setPen(QPen(QColor("#0f172a"), 1.5))
            painter.setBrush(QBrush(QColor("#34d399")))
            for pt in points:
                painter.drawEllipse(pt, 3.8, 3.8)

        painter.setPen(QColor("#94a3b8"))
        painter.setFont(QFont("Segoe UI", 8))
        painter.drawText(
            QRectF(left_pad, top_pad + plot_h + 8, 120, 18),
            align_left(),
            f"Window 1 (bp {self.windows[0]['start']})",
        )
        painter.drawText(
            QRectF(left_pad + plot_w - 150, top_pad + plot_h + 8, 150, 18),
            align_right(),
            f"Window {n} (bp {self.windows[-1]['end']})",
        )
