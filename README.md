# Bundestagsprotokoll-Checker

Komfortable Anwendung zur Prüfung von Bundestagsprotokollen (PDF) auf bestimmte Inhalte.

## Neu: Grafische Oberfläche

Standardmäßig startet jetzt eine **GUI** mit:
- Eingabefeld für PDF-Link (Bundestag)
- optionaler lokaler PDF-Auswahl
- Eingabefeld für Suchtext
- Ergebnis-Tabelle mit **Seitenzahl** und **komplettem Absatz**

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Start (GUI)

```bash
python3 bundestag_protokoll_checker.py
```

## Optional: CLI-Modus

```bash
python3 bundestag_protokoll_checker.py --cli
```

## Hinweis

Die Qualität der Treffer hängt von der Textauslesbarkeit der PDF ab (Layout/Scanqualität). Für redaktionelle Verifikation sollten Treffer immer im Originaldokument gegengeprüft werden.
