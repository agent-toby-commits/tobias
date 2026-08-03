# API Demo (YouTube ReAct Agent)

Streamlit-Demo für REST & External API Integration unter Single AI Agent Design.

## Setup

```bash
cd ~/tl.de
python3 -m venv apps/api/.venv
source apps/api/.venv/bin/activate
pip install -r apps/api/requirements.txt
```

In `tl.de/.env`:

- `OPENAI_API_KEY`
- `YOUTUBE_API_KEY`

## Start

YouTube-Agent (Port 8505):

```bash
cd ~/tl.de
source apps/api/.venv/bin/activate
streamlit run apps/api/app.py --server.port 8505 --server.address 127.0.0.1
```

ISS Live-Tracker läuft **ohne Streamlit** direkt in `/singleagent/api`
(JavaScript + FastAPI-Proxy `/proxy/open-notify/…`).

Website parallel (Port 8001). YouTube-Demo:

- lokal: `http://127.0.0.1:8505`
- Produktion: `/apps/api` (Reverse Proxy)
