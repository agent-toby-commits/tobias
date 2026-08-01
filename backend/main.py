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


@app.get("/contextandmemory")
def context_and_memory():
    return page_response("contextandmemory", "index.html")


@app.get("/contextandmemory/rag")
def context_and_memory_rag():
    return page_response("contextandmemory", "rag.html")


@app.get("/health")
def health():
    return {"ok": True, "site": SITE_NAME}
