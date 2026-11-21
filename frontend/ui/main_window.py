import os
from frontend.ui.qt_compat import (
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
    QSpinBox,
    QLineEdit,
    QPlainTextEdit,
    QScrollArea,
    QGuiApplication,
    align_left,
    align_center,
    stretch_resize,
    no_edit_triggers,
)
from frontend.bridge.asm_bridge import AssemblyBridge, AssemblyWorker
from frontend.ui.charts import BaseCompositionChart, GcLineChart
from frontend.ui.pdf_report import write_analysis_pdf


APP_STYLESHEET = """
QMainWindow, QWidget#RootCanvas {
    background-color: #0b1120;
    color: #e2e8f0;
    font-family: "Segoe UI", Inter, sans-serif;
}
QFrame#Sidebar {
    background-color: #0f172a;
    border-right: 1px solid #1e293b;
}
QLabel#BrandTitle {
    color: #f8fafc;
    font-size: 18px;
    font-weight: 700;
}
QLabel#BrandSub {
    color: #38bdf8;
    font-size: 11px;
    font-weight: 600;
}
QLabel#NavSection {
    color: #64748b;
    font-size: 11px;
    font-weight: 700;
    padding-top: 10px;
}
QPushButton.NavBtn {
    background-color: transparent;
    color: #94a3b8;
    border: none;
    border-radius: 8px;
    padding: 10px 14px;
    text-align: left;
    font-size: 13px;
    font-weight: 600;
}
QPushButton.NavBtn:hover {
    background-color: #1e293b;
    color: #f8fafc;
}
QPushButton.NavBtn[active="true"] {
    background-color: rgba(56, 189, 248, 0.16);
    color: #38bdf8;
    border-left: 3px solid #38bdf8;
}
QPushButton.NavBtnDisabled {
    background-color: transparent;
    color: #475569;
    border: none;
    border-radius: 8px;
    padding: 9px 14px;
    text-align: left;
    font-size: 12px;
}
QFrame#TopBar {
    background-color: #0f172a;
    border-bottom: 1px solid #1e293b;
}
QLabel#PageHeading {
    color: #f8fafc;
    font-size: 18px;
    font-weight: 700;
}
QLabel#HeaderBadge {
    background-color: #1e293b;
    color: #38bdf8;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 5px 10px;
    font-family: "Cascadia Code", Consolas, monospace;
    font-size: 12px;
}
QPushButton#PrimaryBtn {
    background-color: #0284c7;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 9px 16px;
    font-size: 13px;
    font-weight: 600;
}
QPushButton#PrimaryBtn:hover {
    background-color: #0369a1;
}
QPushButton#PrimaryBtn:disabled {
    background-color: #1e293b;
    color: #64748b;
}
QPushButton#SecondaryBtn {
    background-color: #1e293b;
    color: #e2e8f0;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 12px;
    font-weight: 600;
}
QPushButton#SecondaryBtn:hover {
    background-color: #334155;
}
QFrame.Card {
    background-color: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 12px;
}
QLabel.KpiTitle {
    color: #94a3b8;
    font-size: 12px;
    font-weight: 600;
}
QLabel.KpiValue {
    color: #f8fafc;
    font-size: 24px;
    font-weight: 700;
}
QLabel.KpiSub {
    color: #34d399;
    font-size: 11px;
    font-weight: 600;
}
QLabel.SectionTitle {
    color: #f8fafc;
    font-size: 14px;
    font-weight: 700;
}
QPlainTextEdit.SeqBox {
    background-color: #060a12;
    color: #7dd3fc;
    border: 1px solid #1e293b;
    border-radius: 8px;
    padding: 10px;
    font-family: "Cascadia Code", Consolas, monospace;
    font-size: 12px;
}
QTableWidget {
    background-color: #0b1120;
    color: #e2e8f0;
    border: 1px solid #1e293b;
    border-radius: 8px;
    gridline-color: #1e293b;
    font-size: 12px;
}
QHeaderView::section {
    background-color: #1e293b;
    color: #38bdf8;
    padding: 6px;
    border: none;
    font-weight: 600;
}
QSpinBox, QLineEdit {
    background-color: #0b1120;
    color: #f8fafc;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 5px 10px;
    font-size: 13px;
}
QLabel.HelpText {
    color: #94a3b8;
    font-size: 12px;
}
"""


def format_seq_blocks(seq: str, line_width: int = 80) -> str:
    if not seq:
        return ""
    return "\n".join(seq[i : i + line_width] for i in range(0, len(seq), line_width))


class MainWindow(QMainWindow):
    def __init__(self, project_root: str):
        super().__init__()
        self.bridge = AssemblyBridge(project_root)
        self.active_worker = None
        self.current_fasta_path = ""
        self.current_header = ""
        self.clean_sequence = ""
        self.rev_comp_sequence = ""
        self.rna_sequence = ""
        self.last_windows = []
        self.stats_result = None
        self.gc_result = None
        self.rev_result = None
        self.rna_result = None
        self.codon_result = None
        self.pattern_result = None
        self.similarity_result = None
        self.primer_result = None
        self.second_fasta_path = ""

        self.setWindowTitle("DNA Analyzer Tool — MASM x86 + PyQt Tier 1 Workbench")
        self.resize(1280, 800)
        self.setStyleSheet(APP_STYLESHEET)

        self._build_ui()
        self._update_controls_enabled(False)

    def _make_kpi_card(self, title: str, default_val: str, sub_text: str):
        card = QFrame()
        card.setProperty("class", "Card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        lbl_title = QLabel(title)
        lbl_title.setProperty("class", "KpiTitle")
        lbl_val = QLabel(default_val)
        lbl_val.setProperty("class", "KpiValue")
        lbl_sub = QLabel(sub_text)
        lbl_sub.setProperty("class", "KpiSub")

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_val)
        layout.addWidget(lbl_sub)
        return card, lbl_val, lbl_sub

    def _build_ui(self):
        root = QWidget()
        root.setObjectName("RootCanvas")
        self.setCentralWidget(root)
        main_layout = QHBoxLayout(root)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(245)
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(16, 20, 16, 20)
        sb_layout.setSpacing(6)

        brand = QLabel("DNA Analyzer")
        brand.setObjectName("BrandTitle")
        sub = QLabel("MASM x86 + IRVINE32 ENGINE")
        sub.setObjectName("BrandSub")
        sb_layout.addWidget(brand)
        sb_layout.addWidget(sub)

        sec_t1 = QLabel("TIER 1 — CORE WORKBENCH")
        sec_t1.setObjectName("NavSection")
        sb_layout.addWidget(sec_t1)

        self.nav_buttons = []
        nav_items = [
            "Overview & DNA Stats",
            "GC Window Analysis",
            "2-Bit DNA Compression",
            "Reverse Complement",
            "DNA to RNA Conversion",
            "Codon Translation",
            "Pattern Search",
            "Sequence Similarity",
            "Primer Tm Analysis",
            "PDF Report",
        ]
        for idx, text in enumerate(nav_items):
            btn = QPushButton(text)
            btn.setProperty("class", "NavBtn")
            btn.setProperty("active", "true" if idx == 0 else "false")
            btn.clicked.connect(lambda checked, i=idx: self._switch_page(i))
            sb_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        sec_t2 = QLabel("TEAMMATE EXTENSIONS")
        sec_t2.setObjectName("NavSection")
        sb_layout.addWidget(sec_t2)

        for label in [
            "ORF & Codon Table (Tier 2)",
            "Motif & Restriction Scan (Tier 2)",
            "CpG Island Detector (Tier 3)",
        ]:
            b_dis = QPushButton(label)
            b_dis.setProperty("class", "NavBtnDisabled")
            b_dis.setEnabled(False)
            sb_layout.addWidget(b_dis)

        sb_layout.addStretch(1)

        exe_status = "Engine Ready: DNAAnalyzer.exe" if self.bridge.exe_exists() else "Build Required: backend/build.bat"
        self.lbl_engine_status = QLabel(exe_status)
        self.lbl_engine_status.setStyleSheet(
            "color: #34d399; font-size: 11px; font-weight: 600;"
            if self.bridge.exe_exists()
            else "color: #fbbf24; font-size: 11px; font-weight: 600;"
        )
        sb_layout.addWidget(self.lbl_engine_status)

        main_layout.addWidget(sidebar)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        topbar = QFrame()
        topbar.setObjectName("TopBar")
        topbar.setFixedHeight(66)
        tb_layout = QHBoxLayout(topbar)
        tb_layout.setContentsMargins(24, 10, 24, 10)

        self.lbl_page_title = QLabel("Overview & Basic DNA Statistics")
        self.lbl_page_title.setObjectName("PageHeading")
        tb_layout.addWidget(self.lbl_page_title)
        tb_layout.addStretch(1)

        self.lbl_fasta_badge = QLabel("No FASTA Loaded")
        self.lbl_fasta_badge.setObjectName("HeaderBadge")
        tb_layout.addWidget(self.lbl_fasta_badge)

        self.btn_upload = QPushButton("Upload FASTA File (.fasta / .fa)")
        self.btn_upload.setObjectName("PrimaryBtn")
        self.btn_upload.clicked.connect(self._on_upload_fasta)
        tb_layout.addWidget(self.btn_upload)

        self.btn_pdf = QPushButton("Generate PDF Report")
        self.btn_pdf.setObjectName("SecondaryBtn")
        self.btn_pdf.clicked.connect(self._on_generate_pdf)
        tb_layout.addWidget(self.btn_pdf)

        right_layout.addWidget(topbar)

        self.pages = QStackedWidget()
        self.pages.addWidget(self._build_stats_page())
        self.pages.addWidget(self._build_gc_window_page())
        self.pages.addWidget(self._build_compression_page())
        self.pages.addWidget(self._build_rev_comp_page())
        self.pages.addWidget(self._build_rna_page())
        self.pages.addWidget(self._scroll_page(self._build_codon_page()))
        self.pages.addWidget(self._scroll_page(self._build_pattern_page()))
        self.pages.addWidget(self._scroll_page(self._build_similarity_page()))
        self.pages.addWidget(self._scroll_page(self._build_primer_page()))
        self.pages.addWidget(self._scroll_page(self._build_pdf_page()))

        right_layout.addWidget(self.pages)
        main_layout.addWidget(right_panel)

    def _build_stats_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        kpi_grid = QGridLayout()
        kpi_grid.setSpacing(14)
        c1, self.kpi_len_val, self.kpi_len_sub = self._make_kpi_card("Total Sequence Length", "0 bp", "Upload FASTA to begin")
        c2, self.kpi_gc_val, self.kpi_gc_sub = self._make_kpi_card("GC Content", "0.00%", "G + C canonical ratio")
        c3, self.kpi_at_val, self.kpi_at_sub = self._make_kpi_card("AT Content", "0.00%", "A + T canonical ratio")
        c4, self.kpi_n_val, self.kpi_n_sub = self._make_kpi_card("Ambiguous Bases (N)", "0", "Excluded from GC% denominator")
        kpi_grid.addWidget(c1, 0, 0)
        kpi_grid.addWidget(c2, 0, 1)
        kpi_grid.addWidget(c3, 0, 2)
        kpi_grid.addWidget(c4, 0, 3)
        layout.addLayout(kpi_grid)

        mid_row = QHBoxLayout()
        mid_row.setSpacing(16)

        chart_card = QFrame()
        chart_card.setProperty("class", "Card")
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(16, 14, 16, 14)
        lbl_c = QLabel("Nucleotide Composition Breakdown")
        lbl_c.setProperty("class", "SectionTitle")
        self.base_chart = BaseCompositionChart()
        chart_layout.addWidget(lbl_c)
        chart_layout.addWidget(self.base_chart)
        mid_row.addWidget(chart_card, 3)

        table_card = QFrame()
        table_card.setProperty("class", "Card")
        t_layout = QVBoxLayout(table_card)
        t_layout.setContentsMargins(16, 14, 16, 14)
        lbl_t = QLabel("Base Counts & Percentages")
        lbl_t.setProperty("class", "SectionTitle")
        self.stats_table = QTableWidget(5, 4)
        self.stats_table.setHorizontalHeaderLabels(["Base", "Nucleotide", "Count", "Canonical %"])
        self.stats_table.horizontalHeader().setSectionResizeMode(stretch_resize())
        self.stats_table.setEditTriggers(no_edit_triggers())
        t_layout.addWidget(lbl_t)
        t_layout.addWidget(self.stats_table)
        mid_row.addWidget(table_card, 2)

        layout.addLayout(mid_row)

        seq_card = QFrame()
        seq_card.setProperty("class", "Card")
        s_layout = QVBoxLayout(seq_card)
        s_layout.setContentsMargins(16, 12, 16, 14)
        hdr_row = QHBoxLayout()
        lbl_s = QLabel("Cleaned 5' -> 3' Sequence Buffer (Cached in Session)")
        lbl_s.setProperty("class", "SectionTitle")
        self.btn_copy_clean = QPushButton("Copy Clean Sequence")
        self.btn_copy_clean.setObjectName("SecondaryBtn")
        self.btn_copy_clean.clicked.connect(lambda: self._copy_text(self.clean_sequence))
        hdr_row.addWidget(lbl_s)
        hdr_row.addStretch(1)
        hdr_row.addWidget(self.btn_copy_clean)
        self.txt_clean_seq = QPlainTextEdit()
        self.txt_clean_seq.setProperty("class", "SeqBox")
        self.txt_clean_seq.setReadOnly(True)
        self.txt_clean_seq.setMaximumHeight(130)
        s_layout.addLayout(hdr_row)
        s_layout.addWidget(self.txt_clean_seq)
        layout.addWidget(seq_card)

        return page

    def _build_gc_window_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        ctrl_card = QFrame()
        ctrl_card.setProperty("class", "Card")
        c_layout = QHBoxLayout(ctrl_card)
        c_layout.setContentsMargins(16, 12, 16, 12)
        c_layout.setSpacing(14)

        c_layout.addWidget(QLabel("Window Size (bp):"))
        self.spin_win_size = QSpinBox()
        self.spin_win_size.setRange(1, 1000000)
        self.spin_win_size.setValue(4)
        c_layout.addWidget(self.spin_win_size)

        c_layout.addWidget(QLabel("Step Size (bp):"))
        self.spin_step_size = QSpinBox()
        self.spin_step_size.setRange(1, 1000000)
        self.spin_step_size.setValue(2)
        c_layout.addWidget(self.spin_step_size)

        self.btn_run_gc = QPushButton("Run GC Window Analysis")
        self.btn_run_gc.setObjectName("PrimaryBtn")
        self.btn_run_gc.clicked.connect(self._on_run_gc_window)
        c_layout.addWidget(self.btn_run_gc)

        self.btn_export_gc_csv = QPushButton("Export CSV")
        self.btn_export_gc_csv.setObjectName("SecondaryBtn")
        self.btn_export_gc_csv.clicked.connect(self._on_export_gc_csv)
        c_layout.addWidget(self.btn_export_gc_csv)
        c_layout.addStretch(1)

        self.lbl_gc_summary = QLabel("Ready")
        self.lbl_gc_summary.setStyleSheet("color: #94a3b8; font-weight: 600;")
        c_layout.addWidget(self.lbl_gc_summary)
        layout.addWidget(ctrl_card)

        chart_card = QFrame()
        chart_card.setProperty("class", "Card")
        ch_layout = QVBoxLayout(chart_card)
        ch_layout.setContentsMargins(16, 14, 16, 14)
        lbl_g = QLabel("Local GC% Variation Across Sliding Windows")
        lbl_g.setProperty("class", "SectionTitle")
        self.gc_chart = GcLineChart()
        ch_layout.addWidget(lbl_g)
        ch_layout.addWidget(self.gc_chart)
        layout.addWidget(chart_card)

        tbl_card = QFrame()
        tbl_card.setProperty("class", "Card")
        tb_layout = QVBoxLayout(tbl_card)
        tb_layout.setContentsMargins(16, 14, 16, 14)
        self.gc_table = QTableWidget(0, 6)
        self.gc_table.setHorizontalHeaderLabels(
            ["Window #", "Start (1-based)", "End (1-based)", "GC Count", "GC %", "AT %"]
        )
        self.gc_table.horizontalHeader().setSectionResizeMode(stretch_resize())
        self.gc_table.setEditTriggers(no_edit_triggers())
        tb_layout.addWidget(self.gc_table)
        layout.addWidget(tbl_card)

        return page

    def _build_compression_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        bar = QFrame()
        bar.setProperty("class", "Card")
        b_layout = QHBoxLayout(bar)
        b_layout.setContentsMargins(16, 12, 16, 12)
        lbl_info = QLabel("Two-Part .DNA Binary Encoder: Part 1 (2-Bit Bases) + Part 2 (1-Bit N-Position Mask)")
        lbl_info.setProperty("class", "SectionTitle")
        self.btn_run_comp = QPushButton("Compress Sequence (.dna)")
        self.btn_run_comp.setObjectName("PrimaryBtn")
        self.btn_run_comp.clicked.connect(self._on_run_compression)
        self.btn_save_dna = QPushButton("Save .dna Binary File")
        self.btn_save_dna.setObjectName("SecondaryBtn")
        self.btn_save_dna.clicked.connect(self._on_save_dna_file)
        b_layout.addWidget(lbl_info)
        b_layout.addStretch(1)
        b_layout.addWidget(self.btn_run_comp)
        b_layout.addWidget(self.btn_save_dna)
        layout.addWidget(bar)

        kpis = QGridLayout()
        kpis.setSpacing(14)
        c1, self.comp_orig_val, self.comp_orig_sub = self._make_kpi_card("Original ASCII Size", "0 B", "1 byte per nucleotide")
        c2, self.comp_bin_val, self.comp_bin_sub = self._make_kpi_card("Total .DNA File Size", "0 B", "18B header + Part 1 + Part 2")
        c3, self.comp_save_val, self.comp_save_sub = self._make_kpi_card("Payload Reduction", "0.00%", "Net file savings: 0.00%")
        c4, self.comp_ver_val, self.comp_ver_sub = self._make_kpi_card("Round-Trip Check", "Pending", "XOR Checksum: --")
        kpis.addWidget(c1, 0, 0)
        kpis.addWidget(c2, 0, 1)
        kpis.addWidget(c3, 0, 2)
        kpis.addWidget(c4, 0, 3)
        layout.addLayout(kpis)

        hex_card = QFrame()
        hex_card.setProperty("class", "Card")
        h_layout = QVBoxLayout(hex_card)
        h_layout.setContentsMargins(16, 14, 16, 14)
        lbl_h = QLabel("Binary File Hex Dump Preview (First 32 Bytes: Magic 'DNA2' + Header + Packed Payload)")
        lbl_h.setProperty("class", "SectionTitle")
        self.txt_hex_preview = QPlainTextEdit()
        self.txt_hex_preview.setProperty("class", "SeqBox")
        self.txt_hex_preview.setReadOnly(True)
        self.txt_hex_preview.setMaximumHeight(140)
        h_layout.addWidget(lbl_h)
        h_layout.addWidget(self.txt_hex_preview)
        layout.addWidget(hex_card)
        layout.addStretch(1)

        return page

    def _build_rev_comp_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        bar = QFrame()
        bar.setProperty("class", "Card")
        b_layout = QHBoxLayout(bar)
        b_layout.setContentsMargins(16, 12, 16, 12)
        lbl = QLabel("Antiparallel Reverse Complement (5' -> 3' Opposite Strand)")
        lbl.setProperty("class", "SectionTitle")
        self.btn_run_rc = QPushButton("Generate Reverse Complement")
        self.btn_run_rc.setObjectName("PrimaryBtn")
        self.btn_run_rc.clicked.connect(self._on_run_rev_comp)
        self.btn_copy_rc = QPushButton("Copy Result")
        self.btn_copy_rc.setObjectName("SecondaryBtn")
        self.btn_copy_rc.clicked.connect(lambda: self._copy_text(self.rev_comp_sequence))
        self.btn_export_rc = QPushButton("Export FASTA")
        self.btn_export_rc.setObjectName("SecondaryBtn")
        self.btn_export_rc.clicked.connect(
            lambda: self._export_fasta_seq(f"{self.current_header}_reverse_complement", self.rev_comp_sequence)
        )
        b_layout.addWidget(lbl)
        b_layout.addStretch(1)
        b_layout.addWidget(self.btn_run_rc)
        b_layout.addWidget(self.btn_copy_rc)
        b_layout.addWidget(self.btn_export_rc)
        layout.addWidget(bar)

        card = QFrame()
        card.setProperty("class", "Card")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(16, 14, 16, 14)
        self.lbl_rc_meta = QLabel("Reverse Complement Sequence (5' -> 3'):")
        self.lbl_rc_meta.setProperty("class", "SectionTitle")
        self.txt_rc_seq = QPlainTextEdit()
        self.txt_rc_seq.setProperty("class", "SeqBox")
        self.txt_rc_seq.setReadOnly(True)
        c_layout.addWidget(self.lbl_rc_meta)
        c_layout.addWidget(self.txt_rc_seq)
        layout.addWidget(card)

        return page

    def _build_rna_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        bar = QFrame()
        bar.setProperty("class", "Card")
        b_layout = QHBoxLayout(bar)
        b_layout.setContentsMargins(16, 12, 16, 12)
        lbl = QLabel("Coding-Strand DNA to mRNA Transcription (Thymine T -> Uracil U)")
        lbl.setProperty("class", "SectionTitle")
        self.btn_run_rna = QPushButton("Convert DNA to RNA")
        self.btn_run_rna.setObjectName("PrimaryBtn")
        self.btn_run_rna.clicked.connect(self._on_run_dna_to_rna)
        self.btn_copy_rna = QPushButton("Copy RNA")
        self.btn_copy_rna.setObjectName("SecondaryBtn")
        self.btn_copy_rna.clicked.connect(lambda: self._copy_text(self.rna_sequence))
        self.btn_export_rna = QPushButton("Export RNA FASTA")
        self.btn_export_rna.setObjectName("SecondaryBtn")
        self.btn_export_rna.clicked.connect(
            lambda: self._export_fasta_seq(f"{self.current_header}_RNA", self.rna_sequence)
        )
        b_layout.addWidget(lbl)
        b_layout.addStretch(1)
        b_layout.addWidget(self.btn_run_rna)
        b_layout.addWidget(self.btn_copy_rna)
        b_layout.addWidget(self.btn_export_rna)
        layout.addWidget(bar)

        card = QFrame()
        card.setProperty("class", "Card")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(16, 14, 16, 14)
        self.lbl_rna_meta = QLabel("Transcribed RNA Sequence (5' -> 3'):")
        self.lbl_rna_meta.setProperty("class", "SectionTitle")
        self.txt_rna_seq = QPlainTextEdit()
        self.txt_rna_seq.setProperty("class", "SeqBox")
        self.txt_rna_seq.setReadOnly(True)
        c_layout.addWidget(self.lbl_rna_meta)
        c_layout.addWidget(self.txt_rna_seq)
        layout.addWidget(card)

        return page

    def _scroll_page(self, page: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.setWidget(page)
        return scroll

    def _help_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setWordWrap(True)
        label.setProperty("class", "HelpText")
        return label

    def _prepare_table(self, table: QTableWidget):
        table.horizontalHeader().setSectionResizeMode(stretch_resize())
        table.setEditTriggers(no_edit_triggers())
        table.setWordWrap(True)

    def _fill_table(self, table: QTableWidget, rows: list, columns: list):
        table.setRowCount(len(rows))
        for r_idx, row in enumerate(rows):
            for c_idx, key in enumerate(columns):
                table.setItem(r_idx, c_idx, QTableWidgetItem(str(row.get(key, ""))))

    def _build_codon_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        layout.addWidget(self._help_label(
            "The loaded sequence is treated as the coding strand. Translation starts at base 1 in a fixed reading frame "
            "(codon starts at nucleotide positions 1, 4, 7, and so on). DNA T is transcribed to RNA U, then the RNA is split "
            "into consecutive groups of three using backend/data/codon_table.csv. This does not search for a start codon or "
            "choose another frame. Stop codons are * / Stop. A codon containing N is ? / Ambiguous and is not guessed. "
            "A trailing 1 or 2 bases are shown as an incomplete codon and are not translated."
        ))

        bar = QFrame()
        bar.setProperty("class", "Card")
        b_layout = QHBoxLayout(bar)
        b_layout.setContentsMargins(16, 12, 16, 12)
        self.btn_run_codon = QPushButton("Translate Codons")
        self.btn_run_codon.setObjectName("PrimaryBtn")
        self.btn_run_codon.clicked.connect(self._on_run_codon)
        self.lbl_codon_summary = QLabel("Translation has not been run for this FASTA.")
        self.lbl_codon_summary.setWordWrap(True)
        b_layout.addWidget(self.btn_run_codon)
        b_layout.addWidget(self.lbl_codon_summary, 1)
        layout.addWidget(bar)

        card = QFrame()
        card.setProperty("class", "Card")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(16, 14, 16, 14)
        self.lbl_codon_rna = QLabel("RNA sequence")
        self.lbl_codon_rna.setProperty("class", "SectionTitle")
        self.txt_codon_rna = QPlainTextEdit()
        self.txt_codon_rna.setProperty("class", "SeqBox")
        self.txt_codon_rna.setReadOnly(True)
        self.txt_codon_rna.setMaximumHeight(120)
        c_layout.addWidget(self.lbl_codon_rna)
        c_layout.addWidget(self.txt_codon_rna)
        layout.addWidget(card)

        ordered_card = QFrame()
        ordered_card.setProperty("class", "Card")
        o_layout = QVBoxLayout(ordered_card)
        o_layout.setContentsMargins(16, 14, 16, 14)
        ordered_title = QLabel("Complete codons in order")
        ordered_title.setProperty("class", "SectionTitle")
        self.codon_table = QTableWidget(0, 5)
        self.codon_table.setHorizontalHeaderLabels(["#", "Start (1-based)", "Codon", "Symbol", "Amino acid"])
        self._prepare_table(self.codon_table)
        o_layout.addWidget(ordered_title)
        o_layout.addWidget(self.codon_table)
        layout.addWidget(ordered_card)

        sum_card = QFrame()
        sum_card.setProperty("class", "Card")
        s_layout = QVBoxLayout(sum_card)
        s_layout.setContentsMargins(16, 14, 16, 14)
        sum_title = QLabel("Distinct codons")
        sum_title.setProperty("class", "SectionTitle")
        self.codon_summary_table = QTableWidget(0, 5)
        self.codon_summary_table.setHorizontalHeaderLabels(
            ["Codon", "Symbol", "Amino acid", "Count", "Start positions (1-based)"]
        )
        self._prepare_table(self.codon_summary_table)
        s_layout.addWidget(sum_title)
        s_layout.addWidget(self.codon_summary_table)
        layout.addWidget(sum_card)
        return page

    def _build_pattern_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)
        layout.addWidget(self._help_label(
            "Search the loaded cleaned sequence. The pattern must be nonempty and may contain only A, T, G, C, or N. "
            "Lowercase input is normalized to uppercase. N is a literal base, not a wildcard. "
            "Every overlapping occurrence is reported: after each position the search advances one base. Coordinates are 1-based."
        ))
        bar = QFrame()
        bar.setProperty("class", "Card")
        b_layout = QHBoxLayout(bar)
        b_layout.setContentsMargins(16, 12, 16, 12)
        b_layout.addWidget(QLabel("Pattern:"))
        self.txt_pattern = QLineEdit()
        self.txt_pattern.setPlaceholderText("Example: ATGN")
        self.btn_run_pattern = QPushButton("Search")
        self.btn_run_pattern.setObjectName("PrimaryBtn")
        self.btn_run_pattern.clicked.connect(self._on_run_pattern)
        b_layout.addWidget(self.txt_pattern, 1)
        b_layout.addWidget(self.btn_run_pattern)
        layout.addWidget(bar)
        self.lbl_pattern_summary = QLabel("Enter a pattern and click Search.")
        self.lbl_pattern_summary.setWordWrap(True)
        self.lbl_pattern_summary.setProperty("class", "SectionTitle")
        layout.addWidget(self.lbl_pattern_summary)
        card = QFrame()
        card.setProperty("class", "Card")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(16, 14, 16, 14)
        self.pattern_table = QTableWidget(0, 4)
        self.pattern_table.setHorizontalHeaderLabels(["Occurrence", "Start (1-based)", "End (1-based)", "Matched pattern"])
        self._prepare_table(self.pattern_table)
        c_layout.addWidget(self.pattern_table)
        layout.addWidget(card)
        return page

    def _build_similarity_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)
        layout.addWidget(self._help_label(
            "Positional Similarity. Sequence 1 is the loaded FASTA. Choose a second FASTA to compare. "
            "Both files are parsed and validated in Assembly. Bases are compared from position 1 through the shorter sequence. "
            "This is not an alignment and does not account for insertions or deletions. "
            "similarity percent = matches / compared positions * 100. Extra bases on the longer sequence are unpaired. "
            "Changing either FASTA clears the previous comparison result."
        ))
        bar = QFrame()
        bar.setProperty("class", "Card")
        b_layout = QHBoxLayout(bar)
        b_layout.setContentsMargins(16, 12, 16, 12)
        self.btn_pick_second = QPushButton("Select Second FASTA")
        self.btn_pick_second.setObjectName("PrimaryBtn")
        self.btn_pick_second.clicked.connect(self._on_pick_second_fasta)
        self.btn_run_similarity = QPushButton("Run Positional Comparison")
        self.btn_run_similarity.setObjectName("SecondaryBtn")
        self.btn_run_similarity.clicked.connect(self._on_run_similarity)
        b_layout.addWidget(self.btn_pick_second)
        b_layout.addWidget(self.btn_run_similarity)
        b_layout.addStretch(1)
        layout.addWidget(bar)
        self.lbl_similarity_summary = QLabel("Load a FASTA, then select the second sequence.")
        self.lbl_similarity_summary.setWordWrap(True)
        self.lbl_similarity_summary.setProperty("class", "SectionTitle")
        layout.addWidget(self.lbl_similarity_summary)
        card = QFrame()
        card.setProperty("class", "Card")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(16, 14, 16, 14)
        self.similarity_table = QTableWidget(0, 5)
        self.similarity_table.setHorizontalHeaderLabels(
            ["Type", "Position (1-based)", "Sequence", "Base 1", "Base 2"]
        )
        self._prepare_table(self.similarity_table)
        c_layout.addWidget(self.similarity_table)
        layout.addWidget(card)
        return page

    def _build_primer_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)
        layout.addWidget(self._help_label(
            "Basic Wallace-rule Tm estimate. Every overlapping window of length L in the loaded cleaned sequence is scanned. "
            "Tm (degrees Celsius) = 2 * (A + T) + 4 * (G + C). Windows containing N are skipped and have no numeric Tm. "
            "This educational estimate does not account for salt concentration, primer concentration, or nearest-neighbor effects. "
            "Candidates have not been validated for laboratory use. L must be an integer from 1 through the sequence length."
        ))
        bar = QFrame()
        bar.setProperty("class", "Card")
        b_layout = QHBoxLayout(bar)
        b_layout.setContentsMargins(16, 12, 16, 12)
        b_layout.addWidget(QLabel("Candidate length L:"))
        self.spin_primer_len = QSpinBox()
        self.spin_primer_len.setRange(1, 1000000)
        self.spin_primer_len.setValue(20)
        self.btn_run_primer = QPushButton("Scan Candidate Windows")
        self.btn_run_primer.setObjectName("PrimaryBtn")
        self.btn_run_primer.clicked.connect(self._on_run_primer)
        b_layout.addWidget(self.spin_primer_len)
        b_layout.addWidget(self.btn_run_primer)
        b_layout.addStretch(1)
        layout.addWidget(bar)
        self.lbl_primer_summary = QLabel("Choose L and scan the loaded sequence.")
        self.lbl_primer_summary.setWordWrap(True)
        self.lbl_primer_summary.setProperty("class", "SectionTitle")
        layout.addWidget(self.lbl_primer_summary)
        card = QFrame()
        card.setProperty("class", "Card")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(16, 14, 16, 14)
        self.primer_table = QTableWidget(0, 9)
        self.primer_table.setHorizontalHeaderLabels(
            ["Candidate", "Sequence", "Start", "End", "A", "T", "G", "C", "Tm (C)"]
        )
        self._prepare_table(self.primer_table)
        c_layout.addWidget(self.primer_table)
        layout.addWidget(card)
        return page

    def _build_pdf_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)
        layout.addWidget(self._help_label(
            "Generate a PDF for the loaded FASTA. Biological values come from Assembly reports that have actually been run. "
            "Analyses that have not been run are marked as not run. Python lays out the document and does not recalculate "
            "counts, GC, translation, matches, similarity, or Tm."
        ))
        self.lbl_pdf_status = QLabel("Load a FASTA to generate a report.")
        self.lbl_pdf_status.setWordWrap(True)
        self.lbl_pdf_status.setProperty("class", "SectionTitle")
        layout.addWidget(self.lbl_pdf_status)
        self.btn_pdf_page = QPushButton("Generate PDF Report")
        self.btn_pdf_page.setObjectName("PrimaryBtn")
        self.btn_pdf_page.clicked.connect(self._on_generate_pdf)
        layout.addWidget(self.btn_pdf_page, 0)
        layout.addStretch(1)
        return page

    def _switch_page(self, index: int):
        titles = [
            "Overview & Basic DNA Statistics",
            "GC Window Analysis",
            "2-Bit DNA Compression (.dna)",
            "Reverse Complement (5' -> 3')",
            "DNA to RNA Conversion",
            "Codon Translation",
            "Pattern Search",
            "Sequence Similarity",
            "Primer Tm Analysis",
            "PDF Report",
        ]
        self.pages.setCurrentIndex(index)
        self.lbl_page_title.setText(titles[index])
        for idx, btn in enumerate(self.nav_buttons):
            btn.setProperty("active", "true" if idx == index else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        if index == 5 and self.clean_sequence and self.codon_result is None:
            self._on_run_codon()
        if index == 9:
            self._refresh_pdf_status()

    def _update_controls_enabled(self, enabled: bool):
        for btn in [
            self.btn_copy_clean,
            self.btn_run_gc,
            self.btn_export_gc_csv,
            self.btn_run_comp,
            self.btn_save_dna,
            self.btn_run_rc,
            self.btn_copy_rc,
            self.btn_export_rc,
            self.btn_run_rna,
            self.btn_copy_rna,
            self.btn_export_rna,
            self.btn_run_codon,
            self.btn_run_pattern,
            self.btn_pick_second,
            self.btn_run_similarity,
            self.btn_run_primer,
            self.btn_pdf,
            self.btn_pdf_page,
        ]:
            btn.setEnabled(enabled)

    def _launch_task(self, task_name: str, fn, *args):
        if self.active_worker is not None and self.active_worker.isRunning():
            return False
        self.btn_upload.setEnabled(False)
        self.active_worker = AssemblyWorker(task_name, fn, *args)
        self.active_worker.completed.connect(self._on_task_completed)
        self.active_worker.start()
        return True

    def _on_upload_fasta(self):
        default_dir = os.path.join(self.bridge.project_root, "backend", "sample_data")
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select FASTA Sequence File",
            default_dir if os.path.isdir(default_dir) else self.bridge.project_root,
            "FASTA Files (*.fasta *.fa *.fna *.txt);;All Files (*.*)",
        )
        if not path:
            return
        self.current_fasta_path = path
        self._launch_task("STATS", self.bridge.run_stats_from_fasta, path)

    def _on_run_gc_window(self):
        self._launch_task(
            "GC_WIN",
            self.bridge.run_gc_window,
            self.spin_win_size.value(),
            self.spin_step_size.value(),
        )

    def _on_run_compression(self):
        self._launch_task("COMPRESS", self.bridge.run_compression)

    def _on_run_rev_comp(self):
        self._launch_task("REV_COMP", self.bridge.run_reverse_complement)

    def _on_run_dna_to_rna(self):
        self._launch_task("DNA_TO_RNA", self.bridge.run_dna_to_rna)

    def _on_run_codon(self):
        if not self.clean_sequence:
            return
        self._launch_task("TRANSLATE", self.bridge.run_codon_translation)

    def _on_run_pattern(self):
        if not self.clean_sequence:
            return
        pattern = self.txt_pattern.text()
        self.pattern_result = None
        self.pattern_table.setRowCount(0)
        self.lbl_pattern_summary.setText("Searching...")
        if not self._launch_task("PATTERN", self.bridge.run_pattern_search, pattern):
            return

    def _on_pick_second_fasta(self):
        if not self.current_fasta_path:
            return
        default_dir = os.path.join(self.bridge.project_root, "backend", "sample_data")
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Second FASTA File",
            default_dir if os.path.isdir(default_dir) else self.bridge.project_root,
            "FASTA Files (*.fasta *.fa *.fna *.txt);;All Files (*.*)",
        )
        if not path:
            return
        self.second_fasta_path = path
        self._clear_similarity_view()
        self.lbl_similarity_summary.setText(
            f"Second FASTA selected: {os.path.basename(path)}. Previous comparison result was cleared."
        )
        self._on_run_similarity()

    def _on_run_similarity(self):
        if not self.current_fasta_path or not self.second_fasta_path:
            QMessageBox.warning(self, "Sequence Similarity", "Load the first FASTA and select a second FASTA file.")
            return
        self._clear_similarity_view()
        self._launch_task(
            "SIMILARITY",
            self.bridge.run_similarity,
            self.current_fasta_path,
            self.second_fasta_path,
        )

    def _on_run_primer(self):
        if not self.clean_sequence:
            return
        self.primer_result = None
        self.primer_table.setRowCount(0)
        self.lbl_primer_summary.setText("Scanning candidate windows...")
        self._launch_task("PRIMER_TM", self.bridge.run_primer_tm, self.spin_primer_len.value())

    def _on_task_completed(self, task_name: str, res: dict):
        self.btn_upload.setEnabled(True)
        if res.get("STATUS") != "OK":
            code = res.get("ERROR_CODE", "ERR_UNKNOWN")
            msg = res.get("ERROR_MSG", "Execution failed.")
            pos = res.get("ERROR_POS", "0")
            detail = f"{msg}\n\nError Code: {code}"
            if pos != "0":
                if code == "ERR_INVALID_PATTERN":
                    detail += f"\nPattern position: {pos}"
                else:
                    detail += f"\nFile byte offset: {pos}"
            QMessageBox.critical(self, "DNA Analyzer Error", detail)
            if task_name == "PATTERN":
                self.lbl_pattern_summary.setText(msg)
            elif task_name == "SIMILARITY":
                self.lbl_similarity_summary.setText(msg)
            elif task_name == "PRIMER_TM":
                self.lbl_primer_summary.setText(msg)
            elif task_name == "TRANSLATE":
                self.lbl_codon_summary.setText(msg)
            return

        if task_name == "STATS":
            self._apply_stats_result(res)
        elif task_name == "GC_WIN":
            self._apply_gc_window_result(res)
        elif task_name == "COMPRESS":
            self._apply_compression_result(res)
        elif task_name == "REV_COMP":
            self._apply_rev_comp_result(res)
        elif task_name == "DNA_TO_RNA":
            self._apply_rna_result(res)
        elif task_name == "TRANSLATE":
            self._apply_codon_result(res)
        elif task_name == "PATTERN":
            self._apply_pattern_result(res)
        elif task_name == "SIMILARITY":
            self._apply_similarity_result(res)
        elif task_name == "PRIMER_TM":
            self._apply_primer_result(res)

    def _apply_stats_result(self, res: dict):
        self.stats_result = res
        self.current_header = res.get("HEADER", "Record")
        self.clean_sequence = res.get("CLEAN_SEQUENCE", "")
        seq_len = int(res.get("SEQUENCE_LENGTH", "0"))
        valid_canon = int(res.get("VALID_CANONICAL", "0"))
        ca = int(res.get("COUNT_A", "0"))
        ct = int(res.get("COUNT_T", "0"))
        cg = int(res.get("COUNT_G", "0"))
        cc = int(res.get("COUNT_C", "0"))
        cn = int(res.get("COUNT_N", "0"))

        self.lbl_fasta_badge.setText(f">{self.current_header[:42]}  |  {seq_len:,} bp")
        self.kpi_len_val.setText(f"{seq_len:,} bp")
        self.kpi_len_sub.setText(f"{valid_canon:,} canonical nucleotides")
        self.kpi_gc_val.setText(f"{res.get('GC_PERCENT', '0.00')}%")
        self.kpi_at_val.setText(f"{res.get('AT_PERCENT', '0.00')}%")
        self.kpi_n_val.setText(f"{cn:,}")

        self.base_chart.set_counts({"A": ca, "T": ct, "G": cg, "C": cc, "N": cn})

        rows = [
            ("A", "Adenine", f"{ca:,}", f"{res.get('PCT_A', '0.00')}%"),
            ("T", "Thymine", f"{ct:,}", f"{res.get('PCT_T', '0.00')}%"),
            ("G", "Guanine", f"{cg:,}", f"{res.get('PCT_G', '0.00')}%"),
            ("C", "Cytosine", f"{cc:,}", f"{res.get('PCT_C', '0.00')}%"),
            ("N", "Ambiguous", f"{cn:,}", "Masked"),
        ]
        for r_idx, row_vals in enumerate(rows):
            for c_idx, val in enumerate(row_vals):
                self.stats_table.setItem(r_idx, c_idx, QTableWidgetItem(val))

        self.txt_clean_seq.setPlainText(format_seq_blocks(self.clean_sequence))
        self.spin_win_size.setMaximum(max(1, seq_len))
        self.spin_win_size.setValue(min(100, max(1, seq_len)))
        self.spin_step_size.setValue(min(25, max(1, seq_len // 4 if seq_len >= 4 else 1)))
        self.spin_primer_len.setMaximum(max(1, seq_len))
        self.spin_primer_len.setValue(min(20, max(1, seq_len)))

        self.last_windows = []
        self.gc_result = None
        self.gc_chart.set_windows([])
        self.gc_table.setRowCount(0)
        self.lbl_gc_summary.setText("Ready")
        self.rev_comp_sequence = ""
        self.rev_result = None
        self.txt_rc_seq.clear()
        self.lbl_rc_meta.setText("Reverse Complement Sequence (5' -> 3'):")
        self.rna_sequence = ""
        self.rna_result = None
        self.txt_rna_seq.clear()
        self.lbl_rna_meta.setText("Transcribed RNA Sequence (5' -> 3'):")
        self.txt_hex_preview.clear()
        self.comp_orig_val.setText("0 B")
        self.comp_orig_sub.setText("1 byte per nucleotide")
        self.comp_bin_val.setText("0 B")
        self.comp_bin_sub.setText("18B header + Part 1 + Part 2")
        self.comp_save_val.setText("0.00%")
        self.comp_save_sub.setText("Net file savings: 0.00%")
        self.comp_ver_val.setText("Pending")
        self.comp_ver_sub.setText("XOR Checksum: --")
        self._clear_codon_view()
        self._clear_pattern_view()
        self._clear_similarity_view()
        self._clear_primer_view()
        if self.second_fasta_path:
            self.lbl_similarity_summary.setText(
                f"Sequence 1 changed to {self.current_header} ({seq_len:,} bp). "
                f"Second FASTA remains {os.path.basename(self.second_fasta_path)}. "
                "The previous comparison result was cleared. Run the comparison again."
            )
        else:
            self.lbl_similarity_summary.setText(
                f"Sequence 1: {self.current_header} ({seq_len:,} bp). Select a second FASTA."
            )

        self._update_controls_enabled(True)
        self._switch_page(0)

    def _apply_gc_window_result(self, res: dict):
        windows = res.get("WINDOWS", [])
        self.gc_result = res
        self.last_windows = windows
        self.gc_chart.set_windows(windows)
        self.lbl_gc_summary.setText(f"Computed {len(windows):,} windows")

        self.gc_table.setRowCount(len(windows))
        for r_idx, item in enumerate(windows):
            self.gc_table.setItem(r_idx, 0, QTableWidgetItem(str(item["index"])))
            self.gc_table.setItem(r_idx, 1, QTableWidgetItem(str(item["start"])))
            self.gc_table.setItem(r_idx, 2, QTableWidgetItem(str(item["end"])))
            self.gc_table.setItem(r_idx, 3, QTableWidgetItem(str(item["gc_count"])))
            self.gc_table.setItem(r_idx, 4, QTableWidgetItem(f"{item['gc_pct']:.2f}%"))
            self.gc_table.setItem(r_idx, 5, QTableWidgetItem(f"{item['at_pct']:.2f}%"))

    def _apply_compression_result(self, res: dict):
        orig_b = int(res.get("ORIGINAL_BYTES", "0"))
        tot_b = int(res.get("TOTAL_BIN_BYTES", "0"))
        p1_b = int(res.get("PART1_BASE_BYTES", "0"))
        p2_b = int(res.get("PART2_NMASK_BYTES", "0"))
        verified = res.get("ROUNDTRIP_VERIFIED", "0") == "1"

        self.comp_orig_val.setText(f"{orig_b:,} B")
        self.comp_bin_val.setText(f"{tot_b:,} B")
        self.comp_bin_sub.setText(f"18B hdr + {p1_b}B bases + {p2_b}B N-mask")
        self.comp_save_val.setText(f"{res.get('PAYLOAD_SAVED_PCT', '0.00')}%")
        self.comp_save_sub.setText(f"Net file savings: {res.get('SPACE_SAVED_PCT', '0.00')}%")
        self.comp_ver_val.setText("VERIFIED" if verified else "MISMATCH")
        self.comp_ver_sub.setText(f"XOR Checksum: 0x{res.get('CHECKSUM_HEX', '00')}")
        self.txt_hex_preview.setPlainText(res.get("HEX_PREVIEW", ""))

    def _apply_rev_comp_result(self, res: dict):
        self.rev_result = res
        self.rev_comp_sequence = res.get("RESULT_SEQUENCE", "")
        seq_len = int(res.get("SEQUENCE_LENGTH", "0"))
        self.lbl_rc_meta.setText(f"Reverse Complement Sequence (5' -> 3') — {seq_len:,} bp:")
        self.txt_rc_seq.setPlainText(format_seq_blocks(self.rev_comp_sequence))

    def _apply_rna_result(self, res: dict):
        self.rna_result = res
        self.rna_sequence = res.get("RESULT_SEQUENCE", "")
        seq_len = int(res.get("SEQUENCE_LENGTH", "0"))
        u_cnt = int(res.get("URACIL_COUNT", "0"))
        self.lbl_rna_meta.setText(f"Transcribed mRNA Sequence (5' -> 3') — {seq_len:,} nt  |  {u_cnt:,} Uracils (U):")
        self.txt_rna_seq.setPlainText(format_seq_blocks(self.rna_sequence))

    def _clear_codon_view(self):
        self.codon_result = None
        self.txt_codon_rna.clear()
        self.codon_table.setRowCount(0)
        self.codon_summary_table.setRowCount(0)
        self.lbl_codon_summary.setText("Translation has not been run for this FASTA.")
        self.lbl_codon_rna.setText("RNA sequence")

    def _clear_pattern_view(self):
        self.pattern_result = None
        self.pattern_table.setRowCount(0)
        self.lbl_pattern_summary.setText("Enter a pattern and click Search.")

    def _clear_similarity_view(self):
        self.similarity_result = None
        self.similarity_table.setRowCount(0)

    def _clear_primer_view(self):
        self.primer_result = None
        self.primer_table.setRowCount(0)
        self.lbl_primer_summary.setText("Choose L and scan the loaded sequence.")

    def _apply_codon_result(self, res: dict):
        self.codon_result = res
        rna = res.get("RESULT_SEQUENCE", "")
        leftover_n = res.get("LEFTOVER_BASES", "0")
        leftover_seq = res.get("LEFTOVER_SEQ", "")
        trail = "No incomplete trailing codon."
        if leftover_n not in ("0", ""):
            trail = f"Incomplete trailing codon: {leftover_seq} ({leftover_n} base(s), not translated)."
        self.lbl_codon_summary.setText(
            "Coding-strand translation from base 1. "
            f"Complete codons: {res.get('COMPLETE_CODONS', '0')}    "
            f"Stop codons: {res.get('STOP_CODONS', '0')}    "
            f"Ambiguous codons: {res.get('AMBIGUOUS_CODONS', '0')}    "
            f"Leftover bases: {leftover_n}. {trail}"
        )
        self.lbl_codon_rna.setText(f"RNA sequence — {res.get('SEQUENCE_LENGTH', '0')} nt")
        self.txt_codon_rna.setPlainText(format_seq_blocks(rna))
        self._fill_table(self.codon_table, res.get("ORDERED", []), ["index", "start", "codon", "symbol", "name"])
        self._fill_table(
            self.codon_summary_table,
            res.get("SUMMARY", []),
            ["codon", "symbol", "name", "count", "positions"],
        )

    def _apply_pattern_result(self, res: dict):
        self.pattern_result = res
        count = res.get("MATCH_COUNT", "0")
        pattern = res.get("PATTERN", "")
        matches = res.get("MATCHES", [])
        if count == "0":
            self.lbl_pattern_summary.setText(f"No matches found for pattern {pattern}.")
        else:
            self.lbl_pattern_summary.setText(
                f"Pattern {pattern} ({res.get('PATTERN_LENGTH', '')} bp): {count} match(es), including overlaps."
            )
        self._fill_table(self.pattern_table, matches, ["index", "start", "end", "pattern"])

    def _apply_similarity_result(self, res: dict):
        self.similarity_result = res
        self.lbl_similarity_summary.setText(
            "Positional Similarity (not an alignment; indels are not modeled). "
            f"Sequence 1: {res.get('SEQ1_HEADER', '')} ({res.get('SEQ1_LENGTH', '')} bp). "
            f"Sequence 2: {res.get('SEQ2_HEADER', '')} ({res.get('SEQ2_LENGTH', '')} bp). "
            f"Matches: {res.get('MATCH_COUNT', '')}. "
            f"Mismatches: {res.get('MISMATCH_COUNT', '')}. "
            f"Unpaired: {res.get('UNPAIRED_COUNT', '')}. "
            f"Compared positions: {res.get('COMPARED_POSITIONS', '')}. "
            f"Similarity: {res.get('SIMILARITY_PERCENT', '')}%."
        )
        header1 = res.get("SEQ1_HEADER", "Sequence 1")
        header2 = res.get("SEQ2_HEADER", "Sequence 2")
        display_rows = []
        for row in res.get("ROWS", []):
            if row["kind"] == "UNPAIRED":
                seq_name = header1 if row["sequence"] == "1" else header2
                base1 = row["base"] if row["sequence"] == "1" else ""
                base2 = row["base"] if row["sequence"] == "2" else ""
                display_rows.append({
                    "kind": "Unpaired",
                    "position": row["position"],
                    "sequence": seq_name,
                    "base1": base1,
                    "base2": base2,
                })
            else:
                label = "Match" if row["kind"] == "MATCH" else "Mismatch"
                display_rows.append({
                    "kind": label,
                    "position": row["position"],
                    "sequence": "",
                    "base1": row["base1"],
                    "base2": row["base2"],
                })
        self._fill_table(
            self.similarity_table,
            display_rows,
            ["kind", "position", "sequence", "base1", "base2"],
        )

    def _apply_primer_result(self, res: dict):
        self.primer_result = res
        self.lbl_primer_summary.setText(
            "Basic Wallace-rule Tm estimate. "
            "This educational estimate does not account for salt concentration, primer concentration, "
            "or nearest-neighbor effects, and candidates have not been validated for laboratory use. "
            f"L = {res.get('CANDIDATE_LENGTH', '')}. "
            f"Windows scanned: {res.get('TOTAL_WINDOWS', '')}. "
            f"Valid candidates: {res.get('VALID_CANDIDATES', '')}. "
            f"Ambiguous windows skipped: {res.get('AMBIGUOUS_WINDOWS', '')}. "
            f"Minimum Tm: {res.get('MIN_TM', '')}. "
            f"Maximum Tm: {res.get('MAX_TM', '')}. "
            f"Average Tm: {res.get('AVERAGE_TM', '')}."
        )
        self._fill_table(
            self.primer_table,
            res.get("CANDIDATES", []),
            ["index", "sequence", "start", "end", "count_a", "count_t", "count_g", "count_c", "tm"],
        )

    def _refresh_pdf_status(self):
        if not self.stats_result:
            self.lbl_pdf_status.setText("Load a FASTA to generate a report.")
            return
        flags = [
            ("GC window analysis", self.gc_result is not None),
            ("Reverse complement", self.rev_result is not None),
            ("DNA-to-RNA", self.rna_result is not None),
            ("Codon translation", self.codon_result is not None),
            ("Pattern search", self.pattern_result is not None),
            ("Primer Tm analysis", self.primer_result is not None),
            ("Positional similarity", self.similarity_result is not None),
        ]
        lines = [f"Loaded: {os.path.basename(self.current_fasta_path)}"]
        for name, ready in flags:
            lines.append(f"{name}: {'included' if ready else 'not run'}")
        self.lbl_pdf_status.setText("\n".join(lines))

    def _on_generate_pdf(self):
        if not self.stats_result or not self.current_fasta_path:
            QMessageBox.warning(self, "PDF Report", "Load a FASTA file before generating a report.")
            return
        default_name = os.path.splitext(os.path.basename(self.current_fasta_path))[0] + "_report.pdf"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save PDF Report",
            os.path.join(self.bridge.project_root, default_name),
            "PDF Files (*.pdf)",
        )
        if not path:
            return
        if not path.lower().endswith(".pdf"):
            path += ".pdf"
        from datetime import datetime
        payload = {
            "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "filename": self.current_fasta_path,
            "clean_sequence": self.clean_sequence,
            "stats": self.stats_result,
            "gc": self.gc_result,
            "rev": self.rev_result,
            "rna": self.rna_result,
            "codon": self.codon_result,
            "pattern": self.pattern_result,
            "primer": self.primer_result,
            "similarity": self.similarity_result,
        }
        try:
            write_analysis_pdf(path, payload)
        except Exception as exc:
            QMessageBox.critical(self, "PDF Report", str(exc))
            return
        QMessageBox.information(self, "PDF Report", f"Saved PDF report to:\n{path}")

    def _copy_text(self, text: str):
        if not text:
            return
        QGuiApplication.clipboard().setText(text)
        QMessageBox.information(self, "Copied", "Sequence copied to clipboard.")

    def _export_fasta_seq(self, header_name: str, seq: str):
        if not seq:
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export FASTA File",
            os.path.join(self.bridge.project_root, f"{header_name}.fasta"),
            "FASTA Files (*.fasta *.fa)",
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(f">{header_name}\n")
            f.write(format_seq_blocks(seq, 80) + "\n")
        QMessageBox.information(self, "Exported", f"Saved FASTA file to:\n{path}")

    def _on_export_gc_csv(self):
        if not self.last_windows:
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export GC Window CSV",
            os.path.join(self.bridge.project_root, "gc_windows.csv"),
            "CSV Files (*.csv)",
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write("Window,Start_1Based,End_1Based,GC_Count,GC_Percent,AT_Percent\n")
            for item in self.last_windows:
                f.write(
                    f"{item['index']},{item['start']},{item['end']},{item['gc_count']},{item['gc_pct']:.2f},{item['at_pct']:.2f}\n"
                )
        QMessageBox.information(self, "Exported", f"Saved GC window table to:\n{path}")

    def _on_save_dna_file(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Compressed .DNA Binary File",
            os.path.join(self.bridge.project_root, "encoded_sequence.dna"),
            "DNA Binary Files (*.dna)",
        )
        if not path:
            return
        if self.bridge.export_binary_copy(path):
            QMessageBox.information(self, "Saved", f"Saved compressed .DNA file to:\n{path}")
        else:
            QMessageBox.warning(self, "Not Ready", "Run 2-Bit Compression first before saving.")
