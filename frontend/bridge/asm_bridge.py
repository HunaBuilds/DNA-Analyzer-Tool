import os
import shutil
import subprocess
from frontend.ui.qt_compat import QThread, pyqtSignal


class AssemblyBridge:
    def __init__(self, project_root: str):
        self.project_root = os.path.abspath(project_root)
        self.exe_path = os.path.join(self.project_root, "backend", "build", "DNAAnalyzer.exe")
        self.session_dir = os.path.join(self.project_root, "frontend", "session")
        os.makedirs(self.session_dir, exist_ok=True)

    def exe_exists(self) -> bool:
        return os.path.isfile(self.exe_path)

    def _parse_kv_file(self, report_path: str) -> dict:
        if not os.path.isfile(report_path):
            return {
                "STATUS": "ERROR",
                "ERROR_CODE": "ERR_MISSING_OUTPUT",
                "ERROR_MSG": "Assembly executable did not generate an output report file.",
                "ERROR_POS": "0",
            }
        parsed = {}
        with open(report_path, "r", encoding="utf-8", errors="replace") as f:
            for raw_line in f:
                line = raw_line.strip()
                if "=" in line:
                    k, v = line.split("=", 1)
                    parsed[k.strip()] = v.strip()
        return parsed

    def _invoke(self, args: list, report_path: str) -> dict:
        if not self.exe_exists():
            return {
                "STATUS": "ERROR",
                "ERROR_CODE": "ERR_EXE_NOT_FOUND",
                "ERROR_MSG": f"DNAAnalyzer.exe not found at {self.exe_path}. Run backend/build.bat first.",
                "ERROR_POS": "0",
            }
        if os.path.exists(report_path):
            os.remove(report_path)

        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        cmd = [self.exe_path] + args
        try:
            proc = subprocess.run(
                cmd,
                cwd=self.session_dir,
                capture_output=True,
                text=True,
                creationflags=creation_flags,
                timeout=60,
            )
        except Exception as exc:
            return {
                "STATUS": "ERROR",
                "ERROR_CODE": "ERR_SUBPROCESS",
                "ERROR_MSG": str(exc),
                "ERROR_POS": "0",
            }

        data = self._parse_kv_file(report_path)
        data["RETURN_CODE"] = str(proc.returncode)
        return data

    def run_stats_from_fasta(self, fasta_path: str) -> dict:
        report_path = os.path.join(self.session_dir, "stats_report.txt")
        clean_path = os.path.join(self.session_dir, "session_clean.seq")
        args = [
            "-op", "STATS",
            "-in", fasta_path,
            "-out", report_path,
            "-clean", clean_path,
        ]
        res = self._invoke(args, report_path)
        if res.get("STATUS") == "OK" and os.path.isfile(clean_path):
            with open(clean_path, "r", encoding="utf-8") as cf:
                res["CLEAN_SEQUENCE"] = cf.read().strip()
        return res

    def run_gc_window(self, win_size: int, step_size: int) -> dict:
        clean_path = os.path.join(self.session_dir, "session_clean.seq")
        report_path = os.path.join(self.session_dir, "gc_window_report.txt")
        args = [
            "-op", "GC_WIN",
            "-in", clean_path,
            "-raw",
            "-win", str(win_size),
            "-step", str(step_size),
            "-out", report_path,
        ]
        res = self._invoke(args, report_path)
        if res.get("STATUS") == "OK":
            windows = []
            total = int(res.get("TOTAL_WINDOWS", "0"))
            for idx in range(1, total + 1):
                row_str = res.get(f"WINDOW_{idx}", "")
                parts = row_str.split(",")
                if len(parts) == 5:
                    windows.append({
                        "index": idx,
                        "start": int(parts[0]),
                        "end": int(parts[1]),
                        "gc_count": int(parts[2]),
                        "gc_pct": float(parts[3]),
                        "at_pct": float(parts[4]),
                        "gc_pct_text": parts[3],
                        "at_pct_text": parts[4],
                    })
            res["WINDOWS"] = windows
        return res

    def run_compression(self) -> dict:
        clean_path = os.path.join(self.session_dir, "session_clean.seq")
        report_path = os.path.join(self.session_dir, "compress_report.txt")
        bin_path = os.path.join(self.session_dir, "compressed_sequence.dna")
        args = [
            "-op", "COMPRESS",
            "-in", clean_path,
            "-raw",
            "-out", report_path,
            "-bin", bin_path,
        ]
        res = self._invoke(args, report_path)
        if res.get("STATUS") == "OK":
            res["BIN_PATH"] = bin_path
        return res

    def run_reverse_complement(self) -> dict:
        clean_path = os.path.join(self.session_dir, "session_clean.seq")
        report_path = os.path.join(self.session_dir, "rev_comp_report.txt")
        seq_out_path = os.path.join(self.session_dir, "reverse_complement.seq")
        args = [
            "-op", "REV_COMP",
            "-in", clean_path,
            "-raw",
            "-out", report_path,
            "-seqout", seq_out_path,
        ]
        res = self._invoke(args, report_path)
        if res.get("STATUS") == "OK" and os.path.isfile(seq_out_path):
            with open(seq_out_path, "r", encoding="utf-8") as sf:
                res["RESULT_SEQUENCE"] = sf.read().strip()
        return res

    def run_dna_to_rna(self) -> dict:
        clean_path = os.path.join(self.session_dir, "session_clean.seq")
        report_path = os.path.join(self.session_dir, "dna_to_rna_report.txt")
        seq_out_path = os.path.join(self.session_dir, "transcribed_rna.seq")
        args = [
            "-op", "DNA_TO_RNA",
            "-in", clean_path,
            "-raw",
            "-out", report_path,
            "-seqout", seq_out_path,
        ]
        res = self._invoke(args, report_path)
        if res.get("STATUS") == "OK" and os.path.isfile(seq_out_path):
            with open(seq_out_path, "r", encoding="utf-8") as sf:
                res["RESULT_SEQUENCE"] = sf.read().strip()
        return res

    def _read_text(self, path: str) -> str:
        if not os.path.isfile(path):
            return ""
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            return handle.read()

    def _detail_lines(self, path: str) -> list:
        text = self._read_text(path)
        return [line.strip() for line in text.splitlines() if line.strip()]

    def run_codon_translation(self) -> dict:
        clean_path = os.path.join(self.session_dir, "session_clean.seq")
        report_path = os.path.join(self.session_dir, "codon_report.txt")
        detail_path = os.path.join(self.session_dir, "codon_detail.txt")
        seq_out_path = os.path.join(self.session_dir, "codon_rna.seq")
        codon_path = os.path.join(self.project_root, "backend", "data", "codon_table.csv")
        args = [
            "-op", "TRANSLATE",
            "-in", clean_path,
            "-raw",
            "-out", report_path,
            "-detail", detail_path,
            "-seqout", seq_out_path,
            "-codon", codon_path,
        ]
        res = self._invoke(args, report_path)
        if res.get("STATUS") == "OK":
            if os.path.isfile(seq_out_path):
                res["RESULT_SEQUENCE"] = self._read_text(seq_out_path).strip()
            ordered = []
            summary = []
            for line in self._detail_lines(detail_path):
                parts = line.split("|")
                if parts[0] == "ORD" and len(parts) >= 6:
                    ordered.append({
                        "index": parts[1],
                        "start": parts[2],
                        "codon": parts[3],
                        "symbol": parts[4],
                        "name": parts[5],
                    })
                elif parts[0] == "SUM" and len(parts) >= 6:
                    summary.append({
                        "codon": parts[1],
                        "symbol": parts[2],
                        "name": parts[3],
                        "count": parts[4],
                        "positions": parts[5],
                    })
            res["ORDERED"] = ordered
            res["SUMMARY"] = summary
            res["DETAIL_TEXT"] = self._read_text(detail_path)
        return res

    def run_pattern_search(self, pattern: str) -> dict:
        clean_path = os.path.join(self.session_dir, "session_clean.seq")
        report_path = os.path.join(self.session_dir, "pattern_report.txt")
        detail_path = os.path.join(self.session_dir, "pattern_detail.txt")
        args = [
            "-op", "PATTERN",
            "-in", clean_path,
            "-raw",
            "-out", report_path,
            "-detail", detail_path,
            "-pattern", pattern,
        ]
        res = self._invoke(args, report_path)
        if res.get("STATUS") == "OK":
            matches = []
            for line in self._detail_lines(detail_path):
                parts = line.split("|")
                if parts[0] == "MATCH" and len(parts) >= 5:
                    matches.append({
                        "index": parts[1],
                        "start": parts[2],
                        "end": parts[3],
                        "pattern": parts[4],
                    })
            res["MATCHES"] = matches
        return res

    def run_similarity(self, fasta_path: str, second_fasta_path: str) -> dict:
        report_path = os.path.join(self.session_dir, "similarity_report.txt")
        detail_path = os.path.join(self.session_dir, "similarity_detail.txt")
        args = [
            "-op", "SIMILARITY",
            "-in", fasta_path,
            "-in2", second_fasta_path,
            "-out", report_path,
            "-detail", detail_path,
        ]
        res = self._invoke(args, report_path)
        if res.get("STATUS") == "OK":
            rows = []
            for line in self._detail_lines(detail_path):
                parts = line.split("|")
                if parts[0] != "ROW" or len(parts) < 5:
                    continue
                kind = parts[1]
                if kind == "UNPAIRED":
                    rows.append({
                        "kind": kind,
                        "position": parts[2],
                        "sequence": parts[3],
                        "base": parts[4],
                    })
                else:
                    rows.append({
                        "kind": kind,
                        "position": parts[2],
                        "base1": parts[3],
                        "base2": parts[4],
                    })
            res["ROWS"] = rows
        return res

    def run_primer_tm(self, length: int) -> dict:
        clean_path = os.path.join(self.session_dir, "session_clean.seq")
        report_path = os.path.join(self.session_dir, "primer_report.txt")
        detail_path = os.path.join(self.session_dir, "primer_detail.txt")
        args = [
            "-op", "PRIMER_TM",
            "-in", clean_path,
            "-raw",
            "-len", str(length),
            "-out", report_path,
            "-detail", detail_path,
        ]
        res = self._invoke(args, report_path)
        if res.get("STATUS") == "OK":
            candidates = []
            for line in self._detail_lines(detail_path):
                parts = line.split("|", 9)
                if parts[0] == "CAND" and len(parts) >= 10:
                    candidates.append({
                        "index": parts[1],
                        "start": parts[2],
                        "end": parts[3],
                        "count_a": parts[4],
                        "count_t": parts[5],
                        "count_g": parts[6],
                        "count_c": parts[7],
                        "tm": parts[8],
                        "sequence": parts[9],
                    })
            res["CANDIDATES"] = candidates
        return res

    def export_binary_copy(self, dest_path: str) -> bool:
        src = os.path.join(self.session_dir, "compressed_sequence.dna")
        if not os.path.isfile(src):
            return False
        shutil.copyfile(src, dest_path)
        return True


class AssemblyWorker(QThread):
    completed = pyqtSignal(str, dict)

    def __init__(self, task_name: str, fn, *args):
        super().__init__()
        self.task_name = task_name
        self.fn = fn
        self.args = args

    def run(self):
        result = self.fn(*self.args)
        self.completed.emit(self.task_name, result)
