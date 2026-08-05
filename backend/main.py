"""tobiaslampe.de – persönliche Website (statisches Frontend)."""

from __future__ import annotations

from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT / "frontend"
PAGES_DIR = FRONTEND_DIR / "pages"

SITE_NAME = "Tobias Lampe"
OPEN_NOTIFY_BASE = "http://api.open-notify.org"
WHERE_THE_ISS_URL = "https://api.wheretheiss.at/v1/satellites/25544"

app = FastAPI(title="tobiaslampe.de")
app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")


def page_response(*parts: str) -> FileResponse:
    path = PAGES_DIR.joinpath(*parts)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Seite nicht gefunden")
    return FileResponse(path)


async def _fetch_json(url: str, *, timeout: float = 5.0) -> dict:
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError(f"Unerwartete Antwort von {url}")
        return data


async def _proxy_open_notify(path: str) -> dict:
    url = f"{OPEN_NOTIFY_BASE}/{path.lstrip('/')}"
    try:
        return await _fetch_json(url)
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Open-Notify nicht erreichbar: {exc}",
        ) from exc


async def _iss_position() -> tuple[float, float, int | None]:
    """ISS-Koordinaten: Open Notify zuerst, sonst Where The ISS At."""
    errors: list[str] = []
    try:
        iss = await _fetch_json(f"{OPEN_NOTIFY_BASE}/iss-now.json")
        position = iss.get("iss_position") or {}
        return (
            float(position["latitude"]),
            float(position["longitude"]),
            iss.get("timestamp"),
        )
    except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
        errors.append(f"open-notify: {exc}")

    try:
        iss = await _fetch_json(WHERE_THE_ISS_URL)
        return float(iss["latitude"]), float(iss["longitude"]), iss.get("timestamp")
    except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
        errors.append(f"wheretheiss: {exc}")

    raise HTTPException(
        status_code=502,
        detail="ISS-Position nicht erreichbar (" + "; ".join(errors) + ")",
    )


@app.get("/proxy/open-notify/astros")
async def proxy_astros():
    return await _proxy_open_notify("astros.json")


@app.get("/proxy/open-notify/iss-now")
async def proxy_iss_now():
    return await _proxy_open_notify("iss-now.json")


@app.get("/proxy/iss-live")
async def proxy_iss_live():
    """Besatzung + ISS-Position in einer Antwort – für die ISS-Demo."""
    try:
        astros = await _fetch_json(f"{OPEN_NOTIFY_BASE}/astros.json")
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Besatzungsdaten nicht erreichbar: {exc}",
        ) from exc

    latitude, longitude, timestamp = await _iss_position()
    people = astros.get("people") or []
    return {
        "number": int(astros.get("number") or len(people)),
        "people": people,
        "latitude": latitude,
        "longitude": longitude,
        "timestamp": timestamp,
    }

@app.get("/")
def index():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/ueber-mich")
def ueber_mich():
    return page_response("ueber-mich.html")


@app.get("/glossar")
def glossar():
    return page_response("glossar.html")


@app.get("/ailab")
def ailab():
    return page_response("ailab", "index.html")


@app.get("/ailab/leanprototyping")
def ailab_lean_prototyping():
    return page_response("ailab", "leanprototyping.html")


@app.get("/ailab/demos")
def ailab_demos():
    return page_response("ailab", "demos.html")


@app.get("/contextandmemory")
def context_and_memory():
    return page_response("contextandmemory", "index.html")


@app.get("/contextandmemory/rag")
def context_and_memory_rag():
    return page_response("contextandmemory", "rag.html")


@app.get("/singleagent")
def single_agent():
    return page_response("singleagent", "index.html")


@app.get("/singleagent/tooling")
def single_agent_tooling():
    return page_response("singleagent", "tooling.html")


@app.get("/singleagent/api")
def single_agent_api():
    return page_response("singleagent", "api.html")


@app.get("/aicoding")
def ai_coding():
    return page_response("aicoding.html")


@app.get("/vibecoding")
def vibe_coding():
    return page_response("vibecoding.html")


@app.get("/datafactory")
def data_factory():
    return page_response("datafactory", "index.html")


@app.get("/datafactory/vectorembedding")
def data_factory_vector_embedding():
    return page_response("datafactory", "vectorembedding.html")


@app.get("/impressum")
def impressum():
    return page_response("impressum.html")


@app.get("/datenschutz")
def datenschutz():
    return page_response("datenschutz.html")


@app.get("/health")
def health():
    return {"ok": True, "site": SITE_NAME}
