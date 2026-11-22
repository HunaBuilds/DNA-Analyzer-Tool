try:
    from PyQt6.QtCore import (
        Qt,
        QThread,
        pyqtSignal,
        QRectF,
        QPointF,
    )
    from PyQt6.QtGui import (
        QFont,
        QColor,
        QPainter,
        QPen,
        QBrush,
        QPainterPath,
        QLinearGradient,
        QGuiApplication,
    )
    from PyQt6.QtWidgets import (
        QApplication,
        QMainWindow,
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QGridLayout,
        QLabel,
        QPushButton,
        QFrame,
        QStackedWidget,
        QFileDialog,
        QMessageBox,
        QTableWidget,
        QTableWidgetItem,
        QHeaderView,
        QSpinBox,
        QLineEdit,
        QPlainTextEdit,
        QCheckBox,
        QSizePolicy,
        QScrollArea,
        QSpacerItem,
    )
    QT_VERSION = 6
except ImportError:
    from PyQt5.QtCore import (
        Qt,
        QThread,
        pyqtSignal,
        QRectF,
        QPointF,
    )
    from PyQt5.QtGui import (
        QFont,
        QColor,
        QPainter,
        QPen,
        QBrush,
        QPainterPath,
        QLinearGradient,
        QGuiApplication,
    )
    from PyQt5.QtWidgets import (
        QApplication,
        QMainWindow,
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QGridLayout,
        QLabel,
        QPushButton,
        QFrame,
        QStackedWidget,
        QFileDialog,
        QMessageBox,
        QTableWidget,
        QTableWidgetItem,
        QHeaderView,
        QSpinBox,
        QLineEdit,
        QPlainTextEdit,
        QCheckBox,
        QSizePolicy,
        QScrollArea,
        QSpacerItem,
    )
    QT_VERSION = 5


def align_center():
    if QT_VERSION == 6:
        return Qt.AlignmentFlag.AlignCenter
    return Qt.AlignCenter


def align_left():
    if QT_VERSION == 6:
        return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
    return Qt.AlignLeft | Qt.AlignVCenter


def align_right():
    if QT_VERSION == 6:
        return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
    return Qt.AlignRight | Qt.AlignVCenter


def antialias_hint():
    if QT_VERSION == 6:
        return QPainter.RenderHint.Antialiasing
    return QPainter.Antialiasing


def no_pen():
    if QT_VERSION == 6:
        return Qt.PenStyle.NoPen
    return Qt.NoPen


def dash_pen_style():
    if QT_VERSION == 6:
        return Qt.PenStyle.DashLine
    return Qt.DashLine


def stretch_resize():
    if QT_VERSION == 6:
        return QHeaderView.ResizeMode.Stretch
    return QHeaderView.Stretch


def no_edit_triggers():
    if QT_VERSION == 6:
        return QTableWidget.EditTrigger.NoEditTriggers
    return QTableWidget.NoEditTriggers
