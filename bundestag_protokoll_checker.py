#!/usr/bin/env python3
"""Bundestagsprotokoll-Checker mit grafischer Oberfläche.

Standardmäßig startet eine GUI, in der ein PDF-Link (oder optional eine lokale
PDF-Datei) und ein Suchtext eingegeben werden. Treffer werden mit Seitenzahl
und komplettem Absatz angezeigt.
"""

from __future__ import annotations

import argparse
import re
import sys
import threading
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

import tkinter as tk
from tkinter import filedialog, messagebox, ttk


@dataclass
class MatchResult:
    page: int
    paragraph: str


def validate_pdf_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Der Link muss mit http:// oder https:// beginnen.")


def download_pdf(url: str) -> bytes:
    import requests

    validate_pdf_url(url)
    response = requests.get(url, timeout=45)
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "")
    if "pdf" not in content_type.lower() and not url.lower().endswith(".pdf"):
        raise ValueError(
            "Der Link liefert vermutlich keine PDF-Datei "
            f"(Content-Type: {content_type!r})."
        )
    return response.content


def read_local_pdf(pdf_path: Path) -> bytes:
    if not pdf_path.exists():
        raise FileNotFoundError(f"Datei nicht gefunden: {pdf_path}")
    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError("Bitte eine PDF-Datei auswählen.")
    return pdf_path.read_bytes()


def extract_pages(pdf_bytes: bytes) -> list[str]:
    from pypdf import PdfReader

    reader = PdfReader(BytesIO(pdf_bytes))
    return [page.extract_text() or "" for page in reader.pages]


def split_paragraphs(page_text: str) -> list[str]:
    by_blank_lines = [p.strip() for p in re.split(r"\n\s*\n+", page_text) if p.strip()]
    if by_blank_lines:
        return by_blank_lines

    cleaned = page_text.strip()
    return [cleaned] if cleaned else []


def find_matches(pages: list[str], query: str) -> list[MatchResult]:
    query_norm = query.casefold()
    results: list[MatchResult] = []

    for page_number, page_text in enumerate(pages, start=1):
        for paragraph in split_paragraphs(page_text):
            if query_norm in paragraph.casefold():
                paragraph_clean = re.sub(r"\s+", " ", paragraph).strip()
                results.append(MatchResult(page=page_number, paragraph=paragraph_clean))

    return results


def run_search(pdf_url: str, local_file: str, query: str) -> tuple[str, list[MatchResult]]:
    if not query.strip():
        raise ValueError("Bitte einen Suchtext eingeben.")

    source_label = ""
    if pdf_url.strip():
        source_label = pdf_url.strip()
        pdf_bytes = download_pdf(source_label)
    elif local_file.strip():
        source_label = local_file.strip()
        pdf_bytes = read_local_pdf(Path(source_label))
    else:
        raise ValueError("Bitte einen PDF-Link eingeben oder eine lokale PDF-Datei auswählen.")

    pages = extract_pages(pdf_bytes)
    if not pages:
        raise ValueError("Das PDF enthält keine auslesbaren Seiten.")

    return source_label, find_matches(pages, query)


class BundestagCheckerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Bundestagsprotokoll-Checker")
        self.root.geometry("980x700")

        self.url_var = tk.StringVar()
        self.file_var = tk.StringVar()
        self.query_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Bereit")

        self._build_ui()

    def _build_ui(self) -> None:
        container = ttk.Frame(self.root, padding=12)
        container.pack(fill="both", expand=True)

        ttk.Label(container, text="PDF-Link (Bundestag)").grid(row=0, column=0, sticky="w")
        ttk.Entry(container, textvariable=self.url_var).grid(
            row=1, column=0, columnspan=3, sticky="ew", pady=(0, 8)
        )

        ttk.Label(container, text="oder lokale PDF-Datei").grid(row=2, column=0, sticky="w")
        ttk.Entry(container, textvariable=self.file_var).grid(row=3, column=0, sticky="ew", pady=(0, 8))
        ttk.Button(container, text="Datei wählen", command=self._pick_file).grid(
            row=3, column=1, sticky="w", padx=(8, 0), pady=(0, 8)
        )

        ttk.Label(container, text="Gesuchter Text (String)").grid(row=4, column=0, sticky="w")
        ttk.Entry(container, textvariable=self.query_var).grid(
            row=5, column=0, columnspan=3, sticky="ew", pady=(0, 8)
        )

        button_frame = ttk.Frame(container)
        button_frame.grid(row=6, column=0, columnspan=3, sticky="w", pady=(0, 8))

        self.search_button = ttk.Button(button_frame, text="Suche starten", command=self._start_search)
        self.search_button.pack(side="left")
        ttk.Button(button_frame, text="Felder leeren", command=self._clear_inputs).pack(side="left", padx=(8, 0))

        status = ttk.Label(container, textvariable=self.status_var)
        status.grid(row=7, column=0, columnspan=3, sticky="w", pady=(0, 8))

        columns = ("index", "page", "paragraph")
        self.tree = ttk.Treeview(container, columns=columns, show="headings", height=18)
        self.tree.heading("index", text="#")
        self.tree.heading("page", text="Seite")
        self.tree.heading("paragraph", text="Absatz")
        self.tree.column("index", width=50, anchor="center")
        self.tree.column("page", width=90, anchor="center")
        self.tree.column("paragraph", width=760, anchor="w")

        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=8, column=0, columnspan=2, sticky="nsew")
        scrollbar.grid(row=8, column=2, sticky="ns")

        container.columnconfigure(0, weight=1)
        container.rowconfigure(8, weight=1)

    def _pick_file(self) -> None:
        path = filedialog.askopenfilename(
            title="PDF auswählen",
            filetypes=[("PDF-Dateien", "*.pdf"), ("Alle Dateien", "*.*")],
        )
        if path:
            self.file_var.set(path)

    def _clear_inputs(self) -> None:
        self.url_var.set("")
        self.file_var.set("")
        self.query_var.set("")
        self.status_var.set("Bereit")
        self._clear_results()

    def _clear_results(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

    def _start_search(self) -> None:
        self.search_button.state(["disabled"])
        self.status_var.set("Suche läuft …")
        self._clear_results()

        thread = threading.Thread(target=self._search_worker, daemon=True)
        thread.start()

    def _search_worker(self) -> None:
        try:
            source, matches = run_search(
                pdf_url=self.url_var.get(),
                local_file=self.file_var.get(),
                query=self.query_var.get(),
            )
            self.root.after(0, self._search_success, source, matches)
        except Exception as exc:  # GUI-Fehlerbehandlung
            self.root.after(0, self._search_failed, str(exc))

    def _search_success(self, source: str, matches: list[MatchResult]) -> None:
        for idx, match in enumerate(matches, start=1):
            self.tree.insert("", "end", values=(idx, match.page, match.paragraph))

        if matches:
            self.status_var.set(f"Quelle: {source} | Treffer: {len(matches)}")
        else:
            self.status_var.set(f"Quelle: {source} | Keine Treffer gefunden")
            messagebox.showinfo("Ergebnis", "Keine Treffer gefunden.")

        self.search_button.state(["!disabled"])

    def _search_failed(self, error_message: str) -> None:
        self.status_var.set("Fehler bei der Suche")
        self.search_button.state(["!disabled"])
        messagebox.showerror("Fehler", error_message)


def run_cli() -> int:
    try:
        print("Bundestagsprotokoll-Checker (CLI-Modus)")
        pdf_url = input("Bitte PDF-Link eingeben (leer für lokale Datei): ").strip()
        local_file = ""
        if not pdf_url:
            local_file = input("Bitte lokalen PDF-Pfad eingeben: ").strip()
        query = input("Bitte gesuchten Text eingeben: ").strip()

        source, matches = run_search(pdf_url=pdf_url, local_file=local_file, query=query)

        print(f"\nDokument: {source}")
        print(f"Treffer: {len(matches)}")
        for idx, match in enumerate(matches, start=1):
            print(f"[{idx}] Seite {match.page}\n{match.paragraph}\n")
        return 0
    except Exception as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        return 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bundestagsprotokoll-Checker")
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Startet den alten Konsolenmodus statt der grafischen Oberfläche.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.cli:
        return run_cli()

    root = tk.Tk()
    BundestagCheckerApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
