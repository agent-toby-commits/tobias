# tobiaslampe.de

Persönliche Website von Tobias Lampe (Berlin).

## Stack

- FastAPI (`backend/main.py`) – Seiten aus Markdown + statisches Frontend
- `frontend/` – HTML/CSS
- `content/` – Texte (Markdown)

Analog zu `wortkino`, bewusst schlank und erweiterbar.

## Lokal starten

```bash
cd ~/tobiaslampe.de
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8001
```

Dann: [http://127.0.0.1:8001](http://127.0.0.1:8001)

Port **8001**, damit Wortkino weiter auf **8000** laufen kann.

## Inhalt

- `/` – Startseite (Person, Projekte, Link zu Wortwört)
- Texte in `content/*.md`
