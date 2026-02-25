#!/usr/bin/env python3
"""Interaktiver Checker für Bundestagsprotokolle (PDF).

Ablauf:
1) Fragt zuerst nach dem PDF-Link zum Bundestagsdokument.
2) Fragt danach nach dem gesuchten Text (String).
3) Sucht den Text im Dokument.
4) Gibt Fundstellen mit Seitenzahl und komplettem Absatz aus.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from io import BytesIO
from urllib.parse import urlparse


@dataclass
class MatchResult:
    page: int
    paragraph: str


def ask_non_empty(prompt: str) -> str:
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("Bitte eine Eingabe machen.")


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


def extract_pages(pdf_bytes: bytes) -> list[str]:
    from pypdf import PdfReader

    reader = PdfReader(BytesIO(pdf_bytes))
    pages: list[str] = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return pages


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
        paragraphs = split_paragraphs(page_text)
        for paragraph in paragraphs:
            if query_norm in paragraph.casefold():
                paragraph_clean = re.sub(r"\s+", " ", paragraph).strip()
                results.append(MatchResult(page=page_number, paragraph=paragraph_clean))

    return results


def print_results(url: str, query: str, matches: list[MatchResult]) -> None:
    print("\n--- Ergebnis ---")
    print(f"Dokument: {url}")
    print(f"Suchtext: {query}")
    print(f"Anzahl Fundstellen: {len(matches)}\n")

    if not matches:
        print("Keine Treffer gefunden.")
        return

    for idx, match in enumerate(matches, start=1):
        print(f"[{idx}] Seite {match.page}")
        print(f"Absatz: {match.paragraph}\n")


def main() -> int:
    try:
        print("Bundestagsprotokoll-Checker")
        print("=========================")

        pdf_url = ask_non_empty("Bitte PDF-Link zum Bundestagsdokument eingeben: ")
        query = ask_non_empty("Bitte gesuchten Text (String) eingeben: ")

        pdf_bytes = download_pdf(pdf_url)
        pages = extract_pages(pdf_bytes)

        if not pages:
            print("Fehler: Das PDF enthält keine auslesbaren Seiten.", file=sys.stderr)
            return 1

        matches = find_matches(pages, query)
        print_results(pdf_url, query, matches)
        return 0
    except KeyboardInterrupt:
        print("\nAbbruch durch Benutzer.")
        return 130
    except Exception as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
