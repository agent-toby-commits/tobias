"""Einfache Streamlit-RAG-Demo über die 108 Upanishads.

Voraussetzung: einmalig `python apps/rag/ingest.py` (legt chroma_db/ an).
Zur Laufzeit wird die bestehende Datenbank nur geöffnet – kein Re-Embedding.
"""

from __future__ import annotations

import html
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

# Website-Accent (style.css --accent)
ACCENT = "#3ecfbf"
ANSWER_PLACEHOLDER = "Antwort der Upanischaden"

load_dotenv(ROOT_DIR / ".env")
load_dotenv(APP_DIR / ".env")
_clear_broken_proxies()

SYSTEM_PROMPT = (
    "Du bist ein hilfreicher Assistent. Beantworte die Frage NUR basierend "
    "auf den bereitgestellten Upanischaden (das ist dein Kontext). Wenn du die Antwort nicht weißt, "
    "versuche aus dem Text eine wahrscheinliche Antwort abzuleiten.\n\n"
    "Upanischaden:\n{context}"
)

CUSTOM_CSS = f"""
<style>
  /* Weniger Leerraum im Embed */
  .block-container {{
    padding-top: 1.25rem !important;
    padding-bottom: 1rem !important;
    max-width: 48rem;
  }}
  div[data-testid="stVerticalBlock"] > div {{
    gap: 0.55rem;
  }}
  /* Cyan statt Streamlit-Rot/Primär */
  .stButton > button[kind="primary"],
  .stButton > button[data-testid="baseButton-primary"] {{
    background-color: {ACCENT} !important;
    border-color: {ACCENT} !important;
    color: #041014 !important;
    font-weight: 600;
  }}
  .stButton > button[kind="primary"]:hover,
  .stButton > button[data-testid="baseButton-primary"]:hover {{
    background-color: #2fb5a7 !important;
    border-color: #2fb5a7 !important;
    color: #041014 !important;
  }}
  .stButton > button[kind="primary"]:focus,
  .stButton > button[data-testid="baseButton-primary"]:focus {{
    box-shadow: 0 0 0 0.2rem rgba(62, 207, 191, 0.35) !important;
  }}
  /* Graues Antwortfeld */
  .rag-answer {{
    margin-top: 0.35rem;
    padding: 1rem 1.1rem;
    min-height: 7.5rem;
    border-radius: 6px;
    background: #1a1f29;
    border: 1px solid #2a3342;
    color: #c5ced9;
    font-size: 1.02rem;
    line-height: 1.55;
    white-space: pre-wrap;
  }}
  .rag-answer--placeholder {{
    color: #7a8698;
    font-style: italic;
  }}
</style>
"""


def _db_ready(path: Path) -> bool:
    return path.is_dir() and any(path.iterdir())


@st.cache_resource(show_spinner="Lade Vektordatenbank…")
def get_rag_chain():
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY fehlt."
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

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.5)
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
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    if "answer" not in st.session_state:
        st.session_state.answer = None
    if "context_docs" not in st.session_state:
        st.session_state.context_docs = []

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
        with st.spinner("Suche in den Upanischaden und generiere Antwort…"):
            response = rag_chain.invoke({"input": question.strip()})
        st.session_state.answer = response.get("answer") or ""
        st.session_state.context_docs = response.get("context") or []
    elif ask:
        st.warning("Bitte eine Frage eingeben.")

    answer = st.session_state.answer
    if answer:
        st.markdown(
            f'<div class="rag-answer">{html.escape(answer)}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="rag-answer rag-answer--placeholder">{ANSWER_PLACEHOLDER}</div>',
            unsafe_allow_html=True,
        )

    if st.session_state.context_docs:
        with st.expander('Verwendete Quelltexte ("Chunks")'):
            for i, doc in enumerate(st.session_state.context_docs, start=1):
                page = doc.metadata.get("page", "?")
                st.markdown(f"**Chunk {i}** (Seite {page})")
                st.write(doc.page_content)


if __name__ == "__main__":
    main()
