"""tobiaslampe.de – persönliche Website (statisches Frontend)."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT / "frontend"
PAGES_DIR = FRONTEND_DIR / "pages"

SITE_NAME = "Tobias Lampe"

app = FastAPI(title="tobiaslampe.de")
app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")


def page_response(*parts: str) -> FileResponse:
    path = PAGES_DIR.joinpath(*parts)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Seite nicht gefunden")
    return FileResponse(path)


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


@app.get("/singleagent/langgraph")
def single_agent_langgraph():
    return page_response("singleagent", "langgraph.html")


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
