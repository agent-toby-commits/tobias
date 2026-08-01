"""Einfache Streamlit-RAG-Demo über die 108 Upanishads.

Voraussetzung: einmalig `python apps/rag/ingest.py` (legt chroma_db/ an).
Zur Laufzeit wird die bestehende Datenbank nur geöffnet – kein Re-Embedding.
"""

from __future__ import annotations

import os
from pathlib import Path


def _clear_broken_proxies() -> None:
    """Cursor/Sandbox setzt oft lokale HTTP_PROXY-Werte, die Tiktoken/OpenAI blockieren."""
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

import streamlit as st
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

APP_DIR = Path(__file__).resolve().parent
ROOT_DIR = APP_DIR.parent.parent
CHROMA_DIR = APP_DIR / "chroma_db"

load_dotenv(ROOT_DIR / ".env")
load_dotenv(APP_DIR / ".env")
_clear_broken_proxies()

SYSTEM_PROMPT = (
    "Du bist ein hilfreicher Assistent. Beantworte die Frage NUR basierend "
    "auf dem folgenden bereitgestellten Kontext. Wenn du die Antwort nicht weißt, "
    "sage ehrlich, dass es nicht im Text steht.\n\n"
    "Kontext:\n{context}"
)


def _db_ready(path: Path) -> bool:
    return path.is_dir() and any(path.iterdir())


@st.cache_resource(show_spinner="Lade Vektordatenbank…")
def get_rag_chain():
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY fehlt. Bitte in tl.de/.env setzen und Streamlit neu starten."
        )
    if not _db_ready(CHROMA_DIR):
        raise FileNotFoundError(
            f"Keine Chroma-DB unter {CHROMA_DIR}. "
            "Einmalig ausführen: python apps/rag/ingest.py"
        )

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = Chroma(
        persist_directory=str(CHROMA_DIR),
        embedding_function=embeddings,
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("human", "{input}"),
        ]
    )
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    return create_retrieval_chain(retriever, question_answer_chain)


def main() -> None:
    st.set_page_config(
        page_title="RAG Demo: Antwort aus den Upanischaden",
        page_icon="📜",
        layout="centered",
        initial_sidebar_state="collapsed",
    )
    st.title("RAG Demo: Antwort aus den Upanischaden")
    st.markdown(
        "Texteingabe analog zu ChatGPT etc. Die Antwort wird sich "
        "**ausschließlich** auf den hinduistischen Text der Upanischaden berufen."
    )

    try:
        rag_chain = get_rag_chain()
    except Exception as exc:  # noqa: BLE001 – klare UI-Fehlermeldung
        st.error(str(exc))
        st.stop()

    question = st.text_input(
        "Frage",
        label_visibility="collapsed",
        placeholder="Deine Frage…",
    )
    ask = st.button("Fragen", type="primary")

    if ask and question.strip():
        with st.spinner("Suche Kontext und generiere Antwort…"):
            response = rag_chain.invoke({"input": question.strip()})
        st.subheader("Antwort")
        st.write(response["answer"])
        with st.expander("Verwendete Quellen (Chunks)"):
            for i, doc in enumerate(response.get("context") or [], start=1):
                page = doc.metadata.get("page", "?")
                st.markdown(f"**Chunk {i}** (Seite {page})")
                st.write(doc.page_content)
    elif ask:
        st.warning("Bitte eine Frage eingeben.")


if __name__ == "__main__":
    main()
