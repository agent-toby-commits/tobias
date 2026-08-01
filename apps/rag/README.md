# RAG Streamlit Demo

Frage/Antwort über die *108 Upanishads* (LangChain + Chroma + OpenAI).

**Wichtig:** Chunking/Embeddings laufen **nicht** in der Web-App, sondern einmalig über `ingest.py`. Die fertige `chroma_db/` wird mitdeployt bzw. committed.

## Voraussetzungen

- `OPENAI_API_KEY` in `tl.de/.env`
- PDF unter `apps/rag/data/108upanishads.pdf` (nur für Ingest nötig)
- Python-Venv: `apps/rag/.venv`

## 1. Einmalig: Vektordatenbank bauen

```bash
cd ~/tl.de
source apps/rag/.venv/bin/activate
pip install -r apps/rag/requirements.txt
python apps/rag/ingest.py
```

Neu aufbauen nach PDF-Änderung:

```bash
python apps/rag/ingest.py --force
```

Ergebnis: `apps/rag/chroma_db/` (~100 MB) – mitcommitten und auf den Server ziehen.

## 2. Streamlit starten (lädt nur die DB)

```bash
cd ~/tl.de
source apps/rag/.venv/bin/activate
env -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY -u http_proxy -u https_proxy -u all_proxy \
  streamlit run apps/rag/app.py --server.port 8503
```

Website parallel (Port 8001):

```bash
cd ~/tl.de && source .venv/bin/activate
uvicorn backend.main:app --port 8001 --reload
```

Dann: [http://127.0.0.1:8001/contextandmemory/rag](http://127.0.0.1:8001/contextandmemory/rag)

## Live

1. Repo inkl. `chroma_db/` deployen (oder auf dem Server einmal `ingest.py`).
2. Streamlit dauerhaft starten.
3. Caddy: `/apps/rag` → Streamlit reverse-proxyn.
