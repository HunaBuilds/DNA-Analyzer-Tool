"""Colours and the global stylesheet for the DNA Analyzer window."""

BG_TOP = "#E6F0FC"
BG_BOTTOM = "#C6DBF5"
BG = "#E6F0FC"
SURFACE = "#FFFFFF"
BORDER = "#D3E2F6"
INK = "#0B1F44"
MUTED = "#4B5F82"
FAINT = "#7C8DAA"
NAVY = "#0B2A5B"
NAVY_HOVER = "#143A7B"
ACCENT = "#2F6FE4"
TINT = "#E3EEFF"

FONT_UI = "Segoe UI"
FONT_MONO = "Cascadia Mono"

# One colour per nucleotide, used by the pie chart, tables, sequence viewer and helices.
BASE_FILL = {"A": "#10A58A", "T": "#FF6B4A", "G": "#FFB020", "C": "#3B82F6", "N": "#A1A8C0", "U": "#FF6B4A"}
BASE_TEXT = {"A": "#0B8A73", "T": "#EA5430", "G": "#D98A00", "C": "#2563EB", "N": "#7A84A3", "U": "#EA5430"}
BASE_TINT = {"A": "#DDF5EF", "T": "#FFE6DF", "G": "#FFF1D6", "C": "#E0EBFF", "N": "#ECEEF5", "U": "#FFE6DF"}
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
QWidget#Page, QWidget#Landing { background: transparent; }
QScrollArea { background: transparent; border: none; }
QScrollArea > QWidget { background: transparent; }
QScrollArea > QWidget > QWidget { background: transparent; }
QToolTip { background-color: #FFFFFF; color: @INK@; border: 1px solid @BORDER@; padding: 4px 8px; }
QMessageBox { background-color: @SURFACE@; }
QMessageBox QLabel { color: @INK@; }

/* ---- scrollbars ---- */
QScrollBar:vertical { background: transparent; width: 12px; margin: 2px; }
QScrollBar::handle:vertical { background: #A9C0E4; border-radius: 4px; min-height: 36px; }
QScrollBar::handle:vertical:hover { background: #7FA3DB; }
QScrollBar:horizontal { background: transparent; height: 12px; margin: 2px; }
QScrollBar::handle:horizontal { background: #A9C0E4; border-radius: 4px; min-width: 36px; }
QScrollBar::handle:horizontal:hover { background: #7FA3DB; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0px; height: 0px; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }

/* ---- sidebar ---- */
QFrame#Sidebar {
    background-color: qlineargradient(x1:0, y1:0, x2:0.35, y2:1, stop:0 #11458F, stop:0.5 #0A2C62, stop:1 #061838);
    border: none;
}
QLabel#BrandTitle { font-size: 17px; font-weight: 700; color: #FFFFFF; }
QLabel#BrandSub { font-size: 11px; color: #B7CDEE; }
QLabel#NavSection { color: #FFFFFF; font-size: 13px; font-weight: 700; padding: 14px 8px 4px 8px; }
QFrame#NavPill {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3F86F2, stop:1 #2158C9);
    border: 1px solid #6D9BE6; border-radius: 10px;
}
QFrame#EnginePill { background-color: #1B3A72; border: none; border-radius: 15px; }
QFrame#EnginePillLight { background-color: #FFFFFF; border: 1px solid @BORDER@; border-radius: 15px; }

/* ---- top bar ---- */
QFrame#TopBar { background: transparent; border: none; }
QLabel#PageHeading { font-size: 24px; font-weight: 700; color: @NAVY@; }
QLabel#HeaderBadge {
    background-color: #FFFFFF; color: @NAVY@; border: 1px solid #C9DBF3; border-radius: 17px;
    padding: 7px 14px; font-family: "Cascadia Mono", Consolas, monospace; font-size: 12px; font-weight: 600;
}

/* ---- buttons ---- */
QPushButton#PrimaryBtn {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #153F85, stop:1 #0A2358);
    color: #FFFFFF; border: none; border-radius: 12px;
    padding: 10px 18px; font-size: 13px; font-weight: 700;
}
QPushButton#PrimaryBtn:hover { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2050A0, stop:1 #123070); }
QPushButton#PrimaryBtn:pressed { background-color: #081C47; }
QPushButton#PrimaryBtn:disabled { background-color: #C9D6EA; color: #8FA2C2; }
QPushButton#SecondaryBtn {
    background-color: #FFFFFF; color: @NAVY@; border: 1px solid #C4D8F2; border-radius: 12px;
    padding: 9px 16px; font-size: 12px; font-weight: 700;
}
QPushButton#SecondaryBtn:hover { background-color: #F2F7FF; border-color: #9DBEE8; }
QPushButton#SecondaryBtn:pressed { background-color: #E3EEFF; }
QPushButton#SecondaryBtn:disabled { background-color: #EEF3FA; color: #9DB0CC; border-color: #DCE7F5; }
QPushButton#LinkBtn {
    background: transparent; border: none; color: #2563EB; font-weight: 700;
    padding: 4px 2px; text-align: left;
}
QPushButton#LinkBtn:hover { color: @NAVY@; text-decoration: underline; }
QPushButton#LinkBtn:disabled { color: #9DB0CC; }

/* ---- text ---- */
QFrame.Card { background-color: #FFFFFF; border: 1px solid @BORDER@; border-radius: 16px; }
QLabel.KpiTitle { color: @INK@; font-size: 14px; font-weight: 700; }
QLabel.KpiValue { color: @NAVY@; font-size: 32px; font-weight: 800; }
QLabel.KpiSub { color: @MUTED@; font-size: 12px; }
QLabel.SectionTitle { color: @NAVY@; font-size: 17px; font-weight: 700; }
QLabel.HelpText { color: @MUTED@; font-size: 12px; }
QFrame#InfoBox { background-color: #F5F9FF; border: 1px solid #CFE0F7; border-radius: 12px; }

/* ---- sequence viewer, tables, inputs ---- */
QPlainTextEdit.SeqBox {
    background-color: #FBFDFF; color: @INK@; border: 1px solid #CFE0F7; border-left: 4px solid @ACCENT@;
    border-radius: 10px; padding: 8px 10px;
    font-family: "Cascadia Mono", Consolas, "Courier New", monospace; font-size: 13px;
    selection-background-color: #CFE0FA; selection-color: @INK@;
}
QTableWidget {
    background-color: #FFFFFF; alternate-background-color: #F2F7FE; color: @INK@;
    border: 1px solid #CFE0F7; border-radius: 10px; gridline-color: transparent; font-size: 13px;
    selection-background-color: #D6E5FB; selection-color: @INK@;
}
QTableWidget::item { padding: 4px 8px; border: none; }
QTableWidget::item:hover { background-color: #E8F1FE; }
QHeaderView { background: transparent; }
QHeaderView::section {
    background-color: #0F2F69; color: #FFFFFF; padding: 9px 8px; border: none;
    font-weight: 700; font-size: 13px;
}
QHeaderView::section:first { border-top-left-radius: 9px; }
QHeaderView::section:last { border-top-right-radius: 9px; }
QTableCornerButton::section { background-color: #0F2F69; border: none; }
QSpinBox, QLineEdit {
    background-color: #FFFFFF; color: @INK@; border: 1px solid #BFD3F0; border-radius: 10px;
    padding: 7px 10px; font-size: 13px; min-width: 70px;
}
QSpinBox:focus, QLineEdit:focus { border: 1px solid @ACCENT@; }
QSpinBox::up-button, QSpinBox::down-button { width: 0px; border: none; }

/* ---- landing page ---- */
QFrame#LandingArt {
    background-color: qlineargradient(x1:0, y1:0, x2:0.6, y2:1, stop:0 #11458F, stop:0.55 #0A2C62, stop:1 #061838);
    border: none;
}
QLabel#LandingArtHint { color: #9FC0F0; font-size: 12px; }
QLabel#LandingTitle { font-size: 38px; font-weight: 800; color: @NAVY@; }
QLabel#LandingTagline { font-size: 15px; color: @MUTED@; }
QFrame#DropZone { background-color: #F7FAFF; border: 2px dashed #8FB2E8; border-radius: 20px; }
QFrame#DropZone:hover { border: 2px dashed @ACCENT@; background-color: #FFFFFF; }
QFrame#DropZone[dragging="true"] { background-color: #EAF2FF; border: 2px solid @ACCENT@; }
QLabel#DropTitle { font-size: 18px; font-weight: 700; color: @NAVY@; }
QLabel#DropHint { font-size: 12px; color: @FAINT@; }
"""


def _build_stylesheet() -> str:
    tokens = {
        "BG": BG, "SURFACE": SURFACE, "BORDER": BORDER, "INK": INK, "MUTED": MUTED,
        "FAINT": FAINT, "NAVY": NAVY, "NAVY_HOVER": NAVY_HOVER, "TINT": TINT, "ACCENT": ACCENT,
    }
    qss = _QSS
    for key, value in tokens.items():
        qss = qss.replace(f"@{key}@", value)
    return qss


APP_STYLESHEET = _build_stylesheet()