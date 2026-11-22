"""Colours and the global stylesheet for the DNA Analyzer window."""

BG = "#F4F7FB"
SURFACE = "#FFFFFF"
BORDER = "#E1E7EF"
INK = "#0F1B2D"
MUTED = "#5A6A7F"
FAINT = "#8A97A8"
NAVY = "#14274E"
NAVY_HOVER = "#1F3B78"
TINT = "#EAF1FB"

FONT_UI = "Segoe UI"
FONT_MONO = "Cascadia Mono"

# One colour per nucleotide, used by the pie chart, tables, sequence viewer and helix.
BASE_FILL = {"A": "#2FA66A", "T": "#E5484D", "G": "#F5A524", "C": "#3B82F6", "N": "#94A3B8", "U": "#E5484D"}
BASE_TEXT = {"A": "#1B7F4E", "T": "#C93339", "G": "#A76A00", "C": "#2563C9", "N": "#64748B", "U": "#C93339"}
BASE_TINT = {"A": "#E4F5EC", "T": "#FDE8E9", "G": "#FEF1D9", "C": "#E3EEFE", "N": "#EDF1F6", "U": "#FDE8E9"}
BASE_NAMES = {
    "A": "Adenine (A)",
    "T": "Thymine (T)",
    "G": "Guanine (G)",
    "C": "Cytosine (C)",
    "N": "Ambiguous (N)",
}

_QSS = """
QMainWindow, QWidget#RootCanvas { background-color: @BG@; }
QWidget {
    color: @INK@;
    font-family: "Segoe UI", "Inter", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}
QLabel { background: transparent; }
QWidget#Page, QWidget#Landing { background-color: @BG@; }
QScrollArea { background: transparent; border: none; }
QScrollArea > QWidget > QWidget { background: transparent; }
QToolTip {
    background-color: @SURFACE@; color: @INK@;
    border: 1px solid @BORDER@; padding: 4px 8px;
}
QMessageBox { background-color: @SURFACE@; }
QMessageBox QLabel { color: @INK@; }

/* ---- scrollbars ---- */
QScrollBar:vertical { background: transparent; width: 12px; margin: 2px; }
QScrollBar::handle:vertical { background: #C3CEDC; border-radius: 4px; min-height: 36px; }
QScrollBar::handle:vertical:hover { background: #9FB0C6; }
QScrollBar:horizontal { background: transparent; height: 12px; margin: 2px; }
QScrollBar::handle:horizontal { background: #C3CEDC; border-radius: 4px; min-width: 36px; }
QScrollBar::handle:horizontal:hover { background: #9FB0C6; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0px; height: 0px; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }

/* ---- sidebar ---- */
QFrame#Sidebar { background-color: @SURFACE@; border-right: 1px solid @BORDER@; }
QLabel#BrandTitle { font-size: 16px; font-weight: 700; color: @NAVY@; }
QLabel#BrandSub { font-size: 11px; color: @MUTED@; }
QLabel#NavSection { color: @FAINT@; font-size: 11px; font-weight: 600; padding: 12px 10px 4px 10px; }
QFrame#NavPill { background-color: @TINT@; border: none; border-radius: 8px; }

/* ---- top bar ---- */
QFrame#TopBar { background-color: @SURFACE@; border-bottom: 1px solid @BORDER@; }
QLabel#PageHeading { font-size: 18px; font-weight: 700; color: @INK@; }
QLabel#HeaderBadge {
    background-color: @TINT@; color: @NAVY@; border: 1px solid #D3E1F5; border-radius: 14px;
    padding: 5px 12px; font-family: "Cascadia Mono", Consolas, monospace; font-size: 12px;
}
QPushButton#IconBtn {
    background-color: transparent; border: 1px solid transparent; border-radius: 8px;
    font-size: 18px; color: @MUTED@;
}
QPushButton#IconBtn:hover { background-color: #F1F5FA; color: @INK@; }

/* ---- buttons ---- */
QPushButton#PrimaryBtn {
    background-color: @NAVY@; color: #FFFFFF; border: none; border-radius: 8px;
    padding: 9px 16px; font-size: 13px; font-weight: 600;
}
QPushButton#PrimaryBtn:hover { background-color: @NAVY_HOVER@; }
QPushButton#PrimaryBtn:pressed { background-color: #0E1C3B; }
QPushButton#PrimaryBtn:disabled { background-color: #E5EAF1; color: #9AA7B8; }
QPushButton#SecondaryBtn {
    background-color: @SURFACE@; color: @INK@; border: 1px solid #CBD5E1; border-radius: 8px;
    padding: 8px 14px; font-size: 12px; font-weight: 600;
}
QPushButton#SecondaryBtn:hover { background-color: #F1F5F9; }
QPushButton#SecondaryBtn:pressed { background-color: #E6ECF4; }
QPushButton#SecondaryBtn:disabled { background-color: #F4F7FB; color: #A5B1C2; border-color: #E1E7EF; }
QPushButton#LinkBtn {
    background: transparent; border: none; color: #2563C9; font-weight: 600;
    padding: 4px 2px; text-align: left;
}
QPushButton#LinkBtn:hover { color: @NAVY@; text-decoration: underline; }
QPushButton#LinkBtn:disabled { color: #A5B1C2; }

/* ---- cards and text ---- */
QFrame.Card { background-color: @SURFACE@; border: 1px solid @BORDER@; border-radius: 12px; }
QLabel.KpiTitle { color: @MUTED@; font-size: 12px; font-weight: 600; }
QLabel.KpiValue { color: @INK@; font-size: 26px; font-weight: 700; }
QLabel.KpiSub { color: @FAINT@; font-size: 11px; }
QLabel.SectionTitle { color: @INK@; font-size: 14px; font-weight: 700; }
QLabel.HelpText { color: @MUTED@; font-size: 12px; }
QFrame#InfoBox { background-color: #EEF4FD; border: 1px solid #D6E3F6; border-radius: 10px; }

/* ---- sequence viewer, tables, inputs ---- */
QPlainTextEdit.SeqBox {
    background-color: #FBFCFE; color: @INK@; border: 1px solid @BORDER@; border-radius: 8px;
    padding: 8px 10px; font-family: "Cascadia Mono", Consolas, "Courier New", monospace; font-size: 12px;
    selection-background-color: #CFE0FA; selection-color: @INK@;
}
QTableWidget {
    background-color: @SURFACE@; alternate-background-color: #F7F9FC; color: @INK@;
    border: 1px solid @BORDER@; border-radius: 8px; gridline-color: @BORDER@; font-size: 12px;
    selection-background-color: #DCE8FA; selection-color: @INK@;
}
QTableWidget::item { padding: 4px 8px; border: none; }
QTableWidget::item:hover { background-color: #EEF4FD; }
QHeaderView { background-color: #EEF2F7; }
QHeaderView::section {
    background-color: #EEF2F7; color: @INK@; padding: 8px 8px; border: none;
    border-bottom: 1px solid @BORDER@; font-weight: 600; font-size: 12px;
}
QTableCornerButton::section { background-color: #EEF2F7; border: none; }
QSpinBox, QLineEdit {
    background-color: @SURFACE@; color: @INK@; border: 1px solid #CBD5E1; border-radius: 8px;
    padding: 6px 10px; font-size: 13px; min-width: 70px;
}
QSpinBox:focus, QLineEdit:focus { border: 1px solid #2F6FE4; }
QSpinBox::up-button, QSpinBox::down-button { width: 0px; border: none; }

/* ---- landing page ---- */
QFrame#LandingArt {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #EEF4FD, stop:1 #DCE8F6);
    border: none;
}
QLabel#LandingTitle { font-size: 34px; font-weight: 700; color: @NAVY@; }
QLabel#LandingTagline { font-size: 15px; color: @MUTED@; }
QFrame#DropZone { background-color: @SURFACE@; border: 2px dashed #B9C7DB; border-radius: 16px; }
QFrame#DropZone:hover { border: 2px dashed #7FA6E8; }
QFrame#DropZone[dragging="true"] { background-color: #F2F7FF; border: 2px dashed #2F6FE4; }
QLabel#DropTitle { font-size: 17px; font-weight: 600; color: @INK@; }
QLabel#DropHint { font-size: 12px; color: @FAINT@; }
"""


def _build_stylesheet() -> str:
    tokens = {
        "BG": BG, "SURFACE": SURFACE, "BORDER": BORDER, "INK": INK, "MUTED": MUTED,
        "FAINT": FAINT, "NAVY": NAVY, "NAVY_HOVER": NAVY_HOVER, "TINT": TINT,
    }
    qss = _QSS
    for key, value in tokens.items():
        qss = qss.replace(f"@{key}@", value)
    return qss


APP_STYLESHEET = _build_stylesheet()