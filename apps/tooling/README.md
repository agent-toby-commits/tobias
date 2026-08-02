# Tooling Demo (Escape Agent)

Streamlit-Demo für Tool Binding (`bind_tools`) unter Single AI Agent Design.

## Setup

```bash
cd ~/tl.de
python3 -m venv apps/tooling/.venv
source apps/tooling/.venv/bin/activate
pip install -r apps/tooling/requirements.txt
```

`OPENAI_API_KEY` in der Projekt-`.env` (`tl.de/.env`) oder optional in `apps/tooling/.env`.

Optional: `OPENAI_MODEL` (Default: `gpt-4o-mini`).

## Start

```bash
cd ~/tl.de
source apps/tooling/.venv/bin/activate
streamlit run apps/tooling/app.py --server.port 8504 --server.address 127.0.0.1
```

Website parallel (Port 8001). Die HTML-Seite `/singleagent/tooling` bindet die Demo per iframe ein:

- lokal: `http://127.0.0.1:8504`
- Produktion: `/apps/tooling` (Reverse Proxy)
