# tobiaslampe.de

Persönliche Website von Tobias Lampe (Berlin).

## Stack

- FastAPI (`backend/main.py`) – statisches Frontend + Unterseiten
- `frontend/` – HTML/CSS/Assets
- `apps/rag/` – Streamlit-RAG-Demo (eingebettet auf `/contextandmemory/rag`)

## Lokal starten (Website)

```bash
cd ~/tl.de
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8001
```

Dann: [http://127.0.0.1:8001](http://127.0.0.1:8001)

## RAG-Demo (Streamlit)

Einmalig Vektordatenbank erzeugen (danach mitcommitten/deployen):

```bash
cd ~/tl.de
python3 -m venv apps/rag/.venv
source apps/rag/.venv/bin/activate
pip install -r apps/rag/requirements.txt
# OPENAI_API_KEY in .env (Root)
python apps/rag/ingest.py
```

App starten (öffnet nur die bestehende `chroma_db/`, kein Re-Embedding):

```bash
streamlit run apps/rag/app.py --server.port 8503
```

Details: [`apps/rag/README.md`](apps/rag/README.md)

Live: Streamlit hinter Caddy unter `/apps/rag` reverse-proxyn; `chroma_db/` mit auf den Server bringen.
