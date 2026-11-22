"""Binding-agnostic access to Qt classes that qt_compat does not re-export.

Looks in qt_compat first, then falls back to whichever Qt binding qt_compat
is already using (PyQt5, PyQt6 or PySide6), so two bindings are never mixed.
"""
import importlib

from frontend.ui import qt_compat as _compat

_BINDING = _compat.QWidget.__module__.split(".")[0]
_SUBMODULES = ("QtWidgets", "QtGui", "QtCore")


def get_qt(name):
    obj = getattr(_compat, name, None)
    if obj is not None:
        return obj
    for sub in _SUBMODULES:
        try:
            module = importlib.import_module(f"{_BINDING}.{sub}")
        except ImportError:
            continue
        if hasattr(module, name):
            return getattr(module, name)
    raise ImportError(f"{name} is not available from {_BINDING}")


def enum(owner, scope, name):
    """Resolve Qt5-style (Qt.AlignLeft) and Qt6-style (Qt.AlignmentFlag.AlignLeft) enums."""
    scoped = getattr(owner, scope, None)
    if scoped is not None and hasattr(scoped, name):
        return getattr(scoped, name)
    return getattr(owner, name)


def make_animation(parent, ms, start, end, on_value, easing="OutCubic"):
    """A float animation from start to end that calls on_value(v) on every step."""
    QVariantAnimation = get_qt("QVariantAnimation")
    QEasingCurve = get_qt("QEasingCurve")
    anim = QVariantAnimation(parent)
    anim.setDuration(int(ms))
    anim.setStartValue(float(start))
    anim.setEndValue(float(end))
    anim.setEasingCurve(QEasingCurve(enum(QEasingCurve, "Type", easing)))
    anim.valueChanged.connect(on_value)
    return anim


def event_pos(event):
    """(x, y) of a mouse event on both Qt5 and Qt6."""
    if hasattr(event, "position"):
        p = event.position()
        return p.x(), p.y()
    p = event.pos()
    return float(p.x()), float(p.y())