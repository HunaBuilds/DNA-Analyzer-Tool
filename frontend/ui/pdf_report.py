def _latin(text) -> str:
    return "" if text is None else str(text).encode("latin-1", "replace").decode("latin-1")


def write_analysis_pdf(path: str, report: dict) -> None:
    try:
        from fpdf import FPDF
    except ImportError as exc:
        raise RuntimeError(
            "PDF library fpdf2 is not installed. Install it with: pip install fpdf2"
        ) from exc

    class AnalysisPdf(FPDF):
        def header(self):
            self.set_font("Helvetica", "B", 9)
            self.set_text_color(47, 111, 228)
            self.cell(0, 6, "DNA ANALYZER  /  SEQUENCE REPORT", align="L")
            self.ln(3)
            self.set_draw_color(218, 228, 242)
            self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
            self.ln(4)

        def footer(self):
            self.set_y(-12)
            self.set_font("Helvetica", size=8)
            self.set_text_color(100, 116, 139)
            self.cell(0, 8, f"DNA Analyzer  ·  Page {self.page_no()}", align="C")

    pdf = AnalysisPdf(format="A4")
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.set_margins(14, 14, 14)
    pdf.add_page()
    selected_sections = report.get("selected_sections")

    def heading(text, size=13):
        pdf.ln(2)
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "B", size)
        pdf.set_text_color(11, 42, 91)
        pdf.multi_cell(0, 7, _latin(text))
        pdf.set_draw_color(220, 232, 248)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.set_x(pdf.l_margin)

    def body(text, size=10):
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", size=size)
        pdf.set_text_color(30, 41, 59)
        pdf.multi_cell(0, 5, _latin(text))
        pdf.set_x(pdf.l_margin)

    def mono(text):
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Courier", size=8)
        pdf.set_text_color(15, 23, 42)
        pdf.multi_cell(0, 4, _latin(text if text else ""))
        pdf.set_x(pdf.l_margin)

    def not_run(title):
        if selected_sections is not None:
            key = {
                "GC window analysis": "gc", "Reverse complement": "rev",
                "DNA-to-RNA conversion": "rna", "Codon translation": "codon",
                "Pattern search": "pattern", "Candidate primer Tm analysis": "primer",
                "Sequence similarity": "similarity",
            }.get(title)
            if key not in selected_sections:
                return
        heading(title)
        body("This analysis was not run for the loaded FASTA.")

    heading("DNA Analyzer Report", 16)
    body(f"Generated: {report.get('generated', '')}")
    body(f"Source file: {report.get('filename', '')}")

    stats = report.get("stats") or {}
    heading("Sequence overview")
    body(f"FASTA header: {stats.get('HEADER', '')}")
    body(f"Sequence length: {stats.get('SEQUENCE_LENGTH', '')} bp")
    body(
        "Base counts - "
        f"A: {stats.get('COUNT_A', '')}  "
        f"T: {stats.get('COUNT_T', '')}  "
        f"G: {stats.get('COUNT_G', '')}  "
        f"C: {stats.get('COUNT_C', '')}  "
        f"N: {stats.get('COUNT_N', '')}"
    )
    body(f"GC%: {stats.get('GC_PERCENT', '')}%    AT%: {stats.get('AT_PERCENT', '')}%")
    body("Cleaned sequence (coding strand, 5' to 3'):")
    mono(_wrap(report.get("clean_sequence", ""), 90))

    gc = report.get("gc")
    if not gc:
        not_run("GC window analysis")
    else:
        heading("GC window analysis")
        body(
            f"Window size: {gc.get('WINDOW_SIZE', '')} bp    "
            f"Step size: {gc.get('STEP_SIZE', '')} bp    "
            f"Total windows: {gc.get('TOTAL_WINDOWS', '')}"
        )
        body("Window, start, end, GC count, GC%, AT% (1-based coordinates):")
        lines = ["Window  Start  End  GC count  GC%  AT%"]
        for item in gc.get("WINDOWS", []):
            lines.append(
                f"{item['index']}  {item['start']}  {item['end']}  {item['gc_count']}  "
                f"{item.get('gc_pct_text', item['gc_pct'])}  {item.get('at_pct_text', item['at_pct'])}"
            )
        mono("\n".join(lines))

    rev = report.get("rev")
    if not rev:
        not_run("Reverse complement")
    else:
        heading("Reverse complement")
        body(f"Length: {rev.get('SEQUENCE_LENGTH', '')} bp")
        body("Reverse complement sequence (5' to 3'):")
        mono(_wrap(rev.get("RESULT_SEQUENCE", ""), 90))

    rna = report.get("rna")
    if not rna:
        not_run("DNA-to-RNA conversion")
    else:
        heading("DNA-to-RNA conversion")
        body("Coding-strand transcription: every T is replaced by U.")
        body(
            f"Length: {rna.get('SEQUENCE_LENGTH', '')} nt    "
            f"Uracil count: {rna.get('URACIL_COUNT', '')}"
        )
        mono(_wrap(rna.get("RESULT_SEQUENCE", ""), 90))

    codon = report.get("codon")
    if not codon:
        not_run("Codon translation")
    else:
        heading("Codon translation")
        body(
            "The loaded sequence is treated as the coding strand. "
            "Translation starts at base 1 in a fixed reading frame "
            "(codon starts at nucleotide positions 1, 4, 7, ...). "
            "DNA T is transcribed to RNA U before codon lookup against codon_table.csv. "
            "This does not search for a start codon or choose another frame. "
            "Stop codons are shown as * / Stop. A codon containing N is ? / Ambiguous and is not guessed. "
            "A trailing 1 or 2 bases are an incomplete codon and are not translated."
        )
        body(
            f"Complete codons: {codon.get('COMPLETE_CODONS', '')}    "
            f"Stop codons: {codon.get('STOP_CODONS', '')}    "
            f"Ambiguous codons: {codon.get('AMBIGUOUS_CODONS', '')}    "
            f"Leftover bases: {codon.get('LEFTOVER_BASES', '')} "
            f"({codon.get('LEFTOVER_SEQ', '') or 'none'})"
        )
        body("RNA sequence:")
        mono(_wrap(codon.get("RESULT_SEQUENCE", ""), 90))
        body("Codons in order (index, 1-based start, codon, symbol, name):")
        lines = ["#  Start  Codon  Symbol  Name"]
        for item in codon.get("ORDERED", []):
            lines.append(
                f"{item['index']}  {item['start']}  {item['codon']}  {item['symbol']}  {item['name']}"
            )
        mono("\n".join(lines))
        body("Distinct codons (codon, symbol, name, count, 1-based start positions):")
        lines = ["Codon  Symbol  Name  Count  Positions"]
        for item in codon.get("SUMMARY", []):
            lines.append(
                f"{item['codon']}  {item['symbol']}  {item['name']}  {item['count']}  {item['positions']}"
            )
        mono("\n".join(lines))

    pattern = report.get("pattern")
    if not pattern:
        not_run("Pattern search")
    else:
        heading("Pattern search")
        body(
            "N is a literal base, not a wildcard. "
            "Every overlapping occurrence is reported. After each position the search advances one base. "
            "Coordinates are 1-based."
        )
        body(
            f"Pattern: {pattern.get('PATTERN', '')}    "
            f"Length: {pattern.get('PATTERN_LENGTH', '')}    "
            f"Matches: {pattern.get('MATCH_COUNT', '')}"
        )
        matches = pattern.get("MATCHES", [])
        if not matches:
            body("No matches found.")
        else:
            lines = ["Occurrence  Start  End  Pattern"]
            for item in matches:
                lines.append(f"{item['index']}  {item['start']}  {item['end']}  {item['pattern']}")
            mono("\n".join(lines))

    primer = report.get("primer")
    if not primer:
        not_run("Candidate primer Tm analysis")
    else:
        heading("Candidate primer Tm analysis")
        body(primer.get("ESTIMATE", "Basic Wallace-rule Tm estimate"))
        body(
            "Tm (degrees Celsius) = 2 * (A count + T count) + 4 * (G count + C count). "
            "This educational estimate does not account for salt concentration, primer concentration, "
            "or nearest-neighbor effects. Candidates have not been validated for laboratory use. "
            "Windows containing N are skipped and have no numeric Tm. "
            "The average is the sum of candidate Tm values divided by the valid-candidate count, "
            "truncated to two decimal places. If there are no valid candidates, min, max, and average are unavailable."
        )
        body(
            f"Candidate length: {primer.get('CANDIDATE_LENGTH', '')}    "
            f"Windows scanned: {primer.get('TOTAL_WINDOWS', '')}    "
            f"Valid candidates: {primer.get('VALID_CANDIDATES', '')}    "
            f"Ambiguous windows skipped: {primer.get('AMBIGUOUS_WINDOWS', '')}"
        )
        body(
            f"Minimum Tm: {primer.get('MIN_TM', '')}    "
            f"Maximum Tm: {primer.get('MAX_TM', '')}    "
            f"Average Tm: {primer.get('AVERAGE_TM', '')}"
        )
        candidates = primer.get("CANDIDATES", [])
        if candidates:
            lines = ["#  Start  End  A  T  G  C  Tm  Sequence"]
            for item in candidates:
                lines.append(
                    f"{item['index']}  {item['start']}  {item['end']}  "
                    f"{item['count_a']}  {item['count_t']}  {item['count_g']}  {item['count_c']}  "
                    f"{item['tm']}  {item['sequence']}"
                )
            mono("\n".join(lines))
        else:
            body("No valid candidate windows.")

    similarity = report.get("similarity")
    if not similarity:
        not_run("Sequence similarity")
    else:
        heading("Positional similarity")
        body(similarity.get("COMPARISON", "Positional Similarity"))
        body(
            "This is a positional comparison, not a sequence alignment. "
            "It does not account for insertions or deletions. "
            "Positions 1 through the shorter sequence length are compared. "
            "similarity percent = matches / compared positions * 100. "
            "Trailing bases on the longer sequence are unpaired."
        )
        body(f"Sequence 1: {similarity.get('SEQ1_HEADER', '')}    Length: {similarity.get('SEQ1_LENGTH', '')}")
        body(f"Sequence 2: {similarity.get('SEQ2_HEADER', '')}    Length: {similarity.get('SEQ2_LENGTH', '')}")
        body(
            f"Matches: {similarity.get('MATCH_COUNT', '')}    "
            f"Mismatches: {similarity.get('MISMATCH_COUNT', '')}    "
            f"Unpaired: {similarity.get('UNPAIRED_COUNT', '')}    "
            f"Compared positions: {similarity.get('COMPARED_POSITIONS', '')}    "
            f"Similarity: {similarity.get('SIMILARITY_PERCENT', '')}%"
        )
        lines = ["Type  Position  Detail"]
        header1 = similarity.get("SEQ1_HEADER", "1")
        header2 = similarity.get("SEQ2_HEADER", "2")
        for row in similarity.get("ROWS", []):
            if row["kind"] == "UNPAIRED":
                name = header1 if row["sequence"] == "1" else header2
                lines.append(f"UNPAIRED  {row['position']}  {name} base {row['base']}")
            else:
                lines.append(
                    f"{row['kind']}  {row['position']}  {row['base1']} / {row['base2']}"
                )
        mono("\n".join(lines))

    pdf.output(path)


def _wrap(sequence: str, width: int) -> str:
    if not sequence:
        return ""
    return "\n".join(sequence[i : i + width] for i in range(0, len(sequence), width))
