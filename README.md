# Bundestagsprotokoll-Checker

Interaktives Python-Programm zur Prüfung von Bundestagsprotokollen als PDF.

## Was das Programm macht

1. Fragt **zuerst** nach dem PDF-Link zum Bundestagsdokument.
2. Fragt danach nach dem gesuchten Text (String).
3. Durchsucht das Dokument.
4. Gibt pro Fundstelle aus:
   - **Seitenzahl**
   - **kompletten Absatz**

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Start

```bash
python3 bundestag_protokoll_checker.py
```

Danach die beiden Eingaben direkt im Terminal machen:
- PDF-Link
- Suchtext

## Grafische Oberfläche (GUI)

Es gibt jetzt zusätzlich eine GUI-Version auf Basis von **Tkinter** (läuft auch unter Windows):

```bash
python3 bundestag_protokoll_checker_gui.py
```

In der Oberfläche kannst du PDF-Link und Suchtext eintragen und die Treffer direkt im Fenster ansehen.

## Hinweis

Die Qualität der Treffer hängt von der Textauslesbarkeit der PDF ab (Layout/Scanqualität). Für redaktionelle Verifikation sollten Treffer immer im Originaldokument gegengeprüft werden.
