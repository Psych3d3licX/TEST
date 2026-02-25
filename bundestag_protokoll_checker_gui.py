#!/usr/bin/env python3
"""Grafische Oberfläche für den Bundestagsprotokoll-Checker (Tkinter)."""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext

from bundestag_protokoll_checker import download_pdf, extract_pages, find_matches


class CheckerGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Bundestagsprotokoll-Checker (GUI)")
        self.root.geometry("980x700")

        self.url_var = tk.StringVar()
        self.query_var = tk.StringVar()

        self._build_ui()

    def _build_ui(self) -> None:
        frame = tk.Frame(self.root, padx=12, pady=12)
        frame.pack(fill="both", expand=True)

        title = tk.Label(
            frame,
            text="Bundestagsprotokoll-Checker",
            font=("Segoe UI", 16, "bold"),
        )
        title.pack(anchor="w", pady=(0, 12))

        tk.Label(frame, text="PDF-Link:", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        tk.Entry(frame, textvariable=self.url_var, width=120).pack(fill="x", pady=(0, 10))

        tk.Label(frame, text="Suchtext:", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        tk.Entry(frame, textvariable=self.query_var, width=80).pack(fill="x", pady=(0, 10))

        button_row = tk.Frame(frame)
        button_row.pack(fill="x", pady=(0, 10))

        self.search_button = tk.Button(
            button_row,
            text="Dokument prüfen",
            command=self.start_search,
            bg="#0b5ed7",
            fg="white",
            padx=10,
            pady=6,
        )
        self.search_button.pack(side="left")

        self.status_label = tk.Label(button_row, text="Bereit.", fg="#444")
        self.status_label.pack(side="left", padx=12)

        tk.Label(frame, text="Ergebnisse:", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.output = scrolledtext.ScrolledText(frame, wrap="word", font=("Consolas", 10))
        self.output.pack(fill="both", expand=True)
        self.output.insert("1.0", "Hier erscheinen die Treffer inklusive Seite und Absatz.\n")
        self.output.config(state="disabled")

    def _set_status(self, text: str) -> None:
        self.status_label.config(text=text)

    def _set_output(self, text: str) -> None:
        self.output.config(state="normal")
        self.output.delete("1.0", tk.END)
        self.output.insert("1.0", text)
        self.output.config(state="disabled")

    def start_search(self) -> None:
        pdf_url = self.url_var.get().strip()
        query = self.query_var.get().strip()

        if not pdf_url:
            messagebox.showwarning("Eingabe fehlt", "Bitte einen PDF-Link eingeben.")
            return
        if not query:
            messagebox.showwarning("Eingabe fehlt", "Bitte einen Suchtext eingeben.")
            return

        self.search_button.config(state="disabled")
        self._set_status("Lade PDF und suche ...")
        self._set_output("Bitte warten ...")

        worker = threading.Thread(target=self._run_search, args=(pdf_url, query), daemon=True)
        worker.start()

    def _run_search(self, pdf_url: str, query: str) -> None:
        try:
            pdf_bytes = download_pdf(pdf_url)
            pages = extract_pages(pdf_bytes)
            matches = find_matches(pages, query)
            result_text = self._format_result(pdf_url, query, matches)
            self.root.after(0, lambda: self._finish_success(result_text))
        except Exception as exc:
            self.root.after(0, lambda: self._finish_error(str(exc)))

    def _finish_success(self, result_text: str) -> None:
        self._set_output(result_text)
        self._set_status("Fertig.")
        self.search_button.config(state="normal")

    def _finish_error(self, error_text: str) -> None:
        self._set_output(f"Fehler: {error_text}")
        self._set_status("Fehler aufgetreten.")
        self.search_button.config(state="normal")

    @staticmethod
    def _format_result(pdf_url: str, query: str, matches: list) -> str:
        lines = [
            "--- Ergebnis ---",
            f"Dokument: {pdf_url}",
            f"Suchtext: {query}",
            f"Anzahl Fundstellen: {len(matches)}",
            "",
        ]

        if not matches:
            lines.append("Keine Treffer gefunden.")
            return "\n".join(lines)

        for idx, match in enumerate(matches, start=1):
            lines.append(f"[{idx}] Seite {match.page}")
            lines.append(f"Absatz: {match.paragraph}")
            lines.append("")

        return "\n".join(lines)


def main() -> int:
    root = tk.Tk()
    CheckerGUI(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
