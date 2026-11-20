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
    QPlainTextEdit,
    QGuiApplication,
    align_left,
    align_center,
    stretch_resize,
    no_edit_triggers,
)
from frontend.bridge.asm_bridge import AssemblyBridge, AssemblyWorker
from frontend.ui.charts import BaseCompositionChart, GcLineChart


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
QSpinBox {
    background-color: #0b1120;
    color: #f8fafc;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 5px 10px;
    font-size: 13px;
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

        right_layout.addWidget(topbar)

        self.pages = QStackedWidget()
        self.pages.addWidget(self._build_stats_page())
        self.pages.addWidget(self._build_gc_window_page())
        self.pages.addWidget(self._build_compression_page())
        self.pages.addWidget(self._build_rev_comp_page())
        self.pages.addWidget(self._build_rna_page())

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

    def _switch_page(self, index: int):
        titles = [
            "Overview & Basic DNA Statistics",
            "GC Window Analysis",
            "2-Bit DNA Compression (.dna)",
            "Reverse Complement (5' -> 3')",
            "DNA to RNA Conversion",
        ]
        self.pages.setCurrentIndex(index)
        self.lbl_page_title.setText(titles[index])
        for idx, btn in enumerate(self.nav_buttons):
            btn.setProperty("active", "true" if idx == index else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

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
        ]:
            btn.setEnabled(enabled)

    def _launch_task(self, task_name: str, fn, *args):
        if self.active_worker is not None and self.active_worker.isRunning():
            return
        self.btn_upload.setEnabled(False)
        self.active_worker = AssemblyWorker(task_name, fn, *args)
        self.active_worker.completed.connect(self._on_task_completed)
        self.active_worker.start()

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

    def _on_task_completed(self, task_name: str, res: dict):
        self.btn_upload.setEnabled(True)
        if res.get("STATUS") != "OK":
            code = res.get("ERROR_CODE", "ERR_UNKNOWN")
            msg = res.get("ERROR_MSG", "Execution failed.")
            pos = res.get("ERROR_POS", "0")
            detail = f"{msg}\n\nError Code: {code}"
            if pos != "0":
                detail += f"\nFile Byte Offset: {pos}"
            QMessageBox.critical(self, "DNA Analyzer Error", detail)
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

    def _apply_stats_result(self, res: dict):
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

        self.last_windows = []
        self.gc_chart.set_windows([])
        self.gc_table.setRowCount(0)
        self.rev_comp_sequence = ""
        self.txt_rc_seq.clear()
        self.rna_sequence = ""
        self.txt_rna_seq.clear()
        self.txt_hex_preview.clear()

        self._update_controls_enabled(True)
        self._switch_page(0)

    def _apply_gc_window_result(self, res: dict):
        windows = res.get("WINDOWS", [])
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
        self.rev_comp_sequence = res.get("RESULT_SEQUENCE", "")
        seq_len = int(res.get("SEQUENCE_LENGTH", "0"))
        self.lbl_rc_meta.setText(f"Reverse Complement Sequence (5' -> 3') — {seq_len:,} bp:")
        self.txt_rc_seq.setPlainText(format_seq_blocks(self.rev_comp_sequence))

    def _apply_rna_result(self, res: dict):
        self.rna_sequence = res.get("RESULT_SEQUENCE", "")
        seq_len = int(res.get("SEQUENCE_LENGTH", "0"))
        u_cnt = int(res.get("URACIL_COUNT", "0"))
        self.lbl_rna_meta.setText(f"Transcribed mRNA Sequence (5' -> 3') — {seq_len:,} nt  |  {u_cnt:,} Uracils (U):")
        self.txt_rna_seq.setPlainText(format_seq_blocks(self.rna_sequence))

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
