# tobiaslampe.de – Projektüberblick

## Konzept
Persönliche Autoren-Website für Tobias Lampe (Berlin): Einstiegspunkt zu Projekten, vor allem Wortwört (`wortwoert.de`), später erweiterbar um Texte, Vita, Kontakt.

## Struktur
- `content/` – Markdown-Seiten
- `backend/main.py` – FastAPI, rendert Startseite und ggf. Unterseiten
- `frontend/` – HTML/CSS/Assets
- `.venv/`, `requirements.txt` – Python-Setup

## Beziehung zu Wortkino
Liegt auf derselben Ebene wie `~/wortkino`. Eigene Domain, eigener Serverprozess (lokal Port 8001). Kein gemeinsamer Code – nur thematische Verlinkung.
