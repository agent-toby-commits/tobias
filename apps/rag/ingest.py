"""Einmaliges Ingest: PDF → Chunks → Embeddings → chroma_db.

Ausführung (nur wenn die DB fehlt oder das PDF neu ist):

    cd ~/tl.de
    source apps/rag/.venv/bin/activate
    python apps/rag/ingest.py

Optional erzwingen:

    python apps/rag/ingest.py --force
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path


def _clear_broken_proxies() -> None:
    for key in (
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "http_proxy",
        "https_proxy",
        "all_proxy",
        "SOCKS_PROXY",
        "SOCKS5_PROXY",
        "socks_proxy",
        "socks5_proxy",
    ):
        os.environ.pop(key, None)


_clear_broken_proxies()

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

APP_DIR = Path(__file__).resolve().parent
ROOT_DIR = APP_DIR.parent.parent
PDF_PATH = APP_DIR / "data" / "108upanishads.pdf"
DB_PATH = APP_DIR / "chroma_db"

load_dotenv(ROOT_DIR / ".env")
load_dotenv(APP_DIR / ".env")
_clear_broken_proxies()


def db_ready(path: Path) -> bool:
    if not path.is_dir():
        return False
    return any(path.iterdir())


def build_database(*, force: bool = False) -> None:
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY fehlt (tl.de/.env).")

    if not PDF_PATH.is_file():
        raise SystemExit(f"PDF nicht gefunden: {PDF_PATH}")

    if db_ready(DB_PATH) and not force:
        print(f"Chroma-Datenbank existiert bereits unter {DB_PATH}. Kein neues Chunking.")
        print("Neu aufbauen mit: python apps/rag/ingest.py --force")
        return

    if force and DB_PATH.exists():
        print(f"Lösche bestehende Datenbank: {DB_PATH}")
        shutil.rmtree(DB_PATH)

    print(f"Lade PDF: {PDF_PATH}")
    documents = PyPDFLoader(str(PDF_PATH)).load()
    print(f"{len(documents)} Seiten geladen.")

    chunks = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
    ).split_documents(documents)
    print(f"{len(chunks)} Chunks erstellt. Erzeuge Embeddings …")

    Chroma.from_documents(
        documents=chunks,
        embedding=OpenAIEmbeddings(model="text-embedding-3-small"),
        persist_directory=str(DB_PATH),
    )
    print(f"Datenbank erstellt: {DB_PATH}")


def main() -> None:
    parser = argparse.ArgumentParser(description="RAG-Vektordatenbank aus PDF erzeugen")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Bestehende chroma_db löschen und neu aufbauen",
    )
    args = parser.parse_args()
    build_database(force=args.force)


if __name__ == "__main__":
    main()
    sys.exit(0)
