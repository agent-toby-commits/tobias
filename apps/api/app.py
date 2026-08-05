from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from googleapiclient.discovery import build
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

APP_DIR = Path(__file__).resolve().parent
ROOT_DIR = APP_DIR.parent.parent

load_dotenv(ROOT_DIR / ".env")
load_dotenv(APP_DIR / ".env")

# Keys: Projekt-.env (tl.de/.env) oder optional apps/api/.env
# OPENAI_API_KEY  → https://platform.openai.com/api-keys
# YOUTUBE_API_KEY → Google Cloud Console → YouTube Data API v3
YOUTUBE_API_KEY = (os.getenv("YOUTUBE_API_KEY") or "").strip()
OPENAI_API_KEY = (os.getenv("OPENAI_API_KEY") or "").strip()


# ==========================================
# 1. ATOMARE TOOLS FÜR DEN REACT AGENTEN
# ==========================================


@tool
def search_youtube(query: str, max_results: int = 20) -> list[dict]:
    """Sucht YouTube-Videos zu einem Thema. Gibt eine einfache Liste mit IDs, Titeln & URLs zurück."""
    yt = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    res = (
        yt.search()
        .list(q=query, part="id,snippet", type="video", maxResults=max_results)
        .execute()
    )
    return [
        {
            "video_id": i["id"]["videoId"],
            "title": i["snippet"]["title"],
            "url": f"https://youtu.be/{i['id']['videoId']}",
        }
        for i in res.get("items", [])
        if "videoId" in i.get("id", {})
    ]


@tool
def score_and_rank_videos(
    video_ids: list[str],
    w_recency: float = 1.0,
    w_popularity: float = 1.0,
) -> list[dict]:
    """Holt Stats für video_ids, vergibt Ränge für Popularität und Aktualität und sortiert (kleiner Score = besser).

    Jeder Eintrag enthält u. a.:
    - published: Erscheinungsdatum als TT.MM.JJJJ
    - views, likes
    - rank_recency: Platz im Aktualitätsranking (1 = neueste)
    - rank_popularity: Platz im Popularitätsranking (1 = meiste Views)
    - url, title, score
    """
    yt = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    res = (
        yt.videos()
        .list(id=",".join(video_ids), part="snippet,statistics")
        .execute()
    )
    now = datetime.now(timezone.utc)

    raw: list[dict] = []
    for item in res.get("items", []):
        published_dt = datetime.fromisoformat(
            item["snippet"]["publishedAt"].replace("Z", "+00:00")
        )
        stats = item.get("statistics", {})
        raw.append(
            {
                "title": item["snippet"]["title"],
                "url": f"https://youtu.be/{item['id']}",
                "published": published_dt.strftime("%d.%m.%Y"),
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "days": (now - published_dt).days,
            }
        )

    # Ränge vergeben (Platz 1, Platz 2, ...)
    by_pop = sorted(raw, key=lambda x: x["views"], reverse=True)
    by_age = sorted(raw, key=lambda x: x["days"])

    for video in raw:
        rank_popularity = by_pop.index(video) + 1
        rank_recency = by_age.index(video) + 1
        video["rank_popularity"] = rank_popularity
        video["rank_recency"] = rank_recency
        # Borda-Count: Niedrigerer Gesamtscore bedeutet bessere Platzierung
        video["score"] = round(
            (rank_recency * w_recency) + (rank_popularity * w_popularity),
            1,
        )

    return sorted(raw, key=lambda x: x["score"])


def extract_youtube_id(text: str) -> str | None:
    """Extrahiert eine YouTube-Video-ID aus URL oder Freitext."""
    if not text:
        return None
    patterns = (
        r"youtu\.be/([A-Za-z0-9_-]{6,})",
        r"youtube\.com/watch\?v=([A-Za-z0-9_-]{6,})",
        r"youtube\.com/embed/([A-Za-z0-9_-]{6,})",
    )
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None


# ==========================================
# 2. STREAMLIT UI
# ==========================================

def main() -> None:
    st.set_page_config(
        page_title="Youtube API Demo",
        page_icon="▶️",
        initial_sidebar_state="collapsed",
    )
    st.markdown(
        """
        <style>
          /* Streamlit-Chrome im Embed einklappen – ohne Klick-Overlay */
          [data-testid="stToolbar"],
          [data-testid="stDecoration"],
          #MainMenu,
          footer {
            display: none !important;
          }

          header[data-testid="stHeader"] {
            background: transparent !important;
            height: 0 !important;
            min-height: 0 !important;
            border: none !important;
            pointer-events: none !important;
          }

          /* Standard-Luft oben (~6rem) entfernen */
          .stMainBlockContainer,
          [data-testid="stMainBlockContainer"],
          .block-container {
            padding-top: 0.35rem !important;
            padding-bottom: 1rem !important;
          }

          [data-testid="stAppViewContainer"] > .main {
            padding-top: 0 !important;
          }

          .stButton > button,
          .stFormSubmitButton > button,
          [data-testid="stFormSubmitButton"] button {
            background-color: #3ecfbf !important;
            border-color: #3ecfbf !important;
            color: #000000 !important;
            font-weight: 700 !important;
            font-size: 1.05rem !important;
            padding: 0.65rem 1.25rem !important;
            min-height: 2.75rem !important;
            width: 100%;
            box-shadow: 0 0 0 1px rgba(62, 207, 191, 0.35);
          }

          .stButton > button:hover,
          .stFormSubmitButton > button:hover,
          [data-testid="stFormSubmitButton"] button:hover {
            background-color: #2fb5a7 !important;
            border-color: #2fb5a7 !important;
            color: #000000 !important;
          }

          .stButton > button span,
          .stButton > button p,
          .stFormSubmitButton > button span,
          .stFormSubmitButton > button p,
          [data-testid="stFormSubmitButton"] button span,
          [data-testid="stFormSubmitButton"] button p {
            color: #000000 !important;
          }

          /* Suchfeld auffälliger */
          [data-testid="stTextInput"] label p {
            font-size: 1.05rem !important;
            font-weight: 700 !important;
            color: #ffffff !important;
          }

          [data-testid="stTextInput"] input {
            border: 2px solid #3ecfbf !important;
            border-radius: 6px !important;
            background: rgba(62, 207, 191, 0.08) !important;
            color: #ffffff !important;
            font-size: 1.05rem !important;
            padding: 0.7rem 0.85rem !important;
            min-height: 2.75rem !important;
          }

          [data-testid="stTextInput"] input:focus {
            border-color: #5eead4 !important;
            box-shadow: 0 0 0 3px rgba(62, 207, 191, 0.25) !important;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.write(
        "Suche im Freitext-Feld nach einem YouTube-Video und gib mit dem "
        "Schieberegler an, ob es dir eher auf Aktualität oder Popularität "
        "(Views, Likes) des Videos ankommt."
    )

    # Labels per Flexbox – st.columns klappen auf Mobile untereinander
    st.markdown(
        """
        <div style="
            display:flex;
            justify-content:space-between;
            align-items:baseline;
            gap:0.75rem;
            margin-bottom:-0.35rem;
            font-weight:600;
        ">
            <span>Aktualität</span>
            <span>Popularität</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    slider = st.slider(
        "Fokus",
        min_value=-100,
        max_value=100,
        value=0,
        step=1,
        label_visibility="collapsed",
    )
    w_recency = max(0.0, -slider / 10)
    w_popularity = max(0.0, slider / 10)
    # Slider bei 0 → beide Gewichte 0; Mindestgewicht setzen, damit Ranking nicht kollabiert
    if w_recency == 0.0 and w_popularity == 0.0:
        w_recency = 1.0
        w_popularity = 1.0

    with st.form("youtube_search_form", clear_on_submit=False):
        query_input = st.text_input(
            "Suchen:", placeholder="Was ist API?"
        )
        submitted = st.form_submit_button("Video suchen", type="primary")

    DEFAULT_VIDEO_ID = "LodLJQ2sYjo"
    DEFAULT_VIDEO_START_S = 21

    def show_default_video() -> None:
        st.video(
            f"https://www.youtube.com/watch?v={DEFAULT_VIDEO_ID}",
            start_time=DEFAULT_VIDEO_START_S,
        )

    # ==========================================
    # 3. AGENTEN-AUSFÜHRUNG MIT STREAMING
    # ==========================================

    if submitted and not (query_input or "").strip():
        st.warning("Bitte zuerst eine Suchanfrage eingeben.")
        show_default_video()
        return

    if submitted and query_input:
        if not OPENAI_API_KEY:
            st.error(
                "Kein OpenAI API-Key. Lege `OPENAI_API_KEY` in `tl.de/.env` ab "
                "(Key: https://platform.openai.com/api-keys)."
            )
            st.stop()
        if not YOUTUBE_API_KEY:
            st.error(
                "Kein YouTube API-Key. Lege `YOUTUBE_API_KEY` in `tl.de/.env` ab "
                "(Google Cloud → YouTube Data API v3)."
            )
            st.stop()

        llm = ChatOpenAI(
            model="gpt-4o-mini", temperature=0, api_key=OPENAI_API_KEY
        )
        agent = create_react_agent(
            llm,
            [search_youtube, score_and_rank_videos],
            prompt=(
                "Suche erst mit search_youtube, bewerte dann mit "
                "score_and_rank_videos und stelle das TOP-Video mit Link "
                "und Begründung vor.\n\n"
                "Die Begründung MUSS mit genau diesen beiden Zeilen beginnen "
                "(Werte aus dem Ranking-Tool, Platz = rank_recency / "
                "rank_popularity):\n"
                "Erscheinungsdatum: TT.MM.JJJJ - das ist Platz X im "
                "Aktualitätsranking\n"
                "Popularität: X Views und X Likes - das ist Platz X im "
                "Popularitätsranking\n"
                "Danach erst die weitere Begründung."
            ),
        )

        status_box = st.status("🧠 Agent arbeitet...", expanded=True)
        ans_box = st.empty()
        full_res = ""
        top_video_id: str | None = None

        # ReAct-Streaming Schleife
        prompt = (
            f"Suche '{query_input}'. "
            f"Gewichte: w_recency={w_recency}, w_popularity={w_popularity}"
        )
        for chunk, _ in agent.stream(
            {"messages": [("user", prompt)]}, stream_mode="messages"
        ):
            tool_calls = getattr(chunk, "tool_calls", None) or []
            if tool_calls:
                status_box.write(
                    f"⚙️ **Agent führt Tool aus:** `{tool_calls[0]['name']}`"
                )
            elif getattr(chunk, "type", None) == "tool":
                raw = chunk.content
                try:
                    out = json.loads(raw) if isinstance(raw, str) else raw
                except json.JSONDecodeError:
                    out = raw
                count = len(out) if isinstance(out, list) else 1
                status_box.write(
                    f"✅ **Ergebnis (`{chunk.name}`):** {count} Elemente verarbeitet."
                )
                # Top-Treffer aus dem Ranking-Tool für den Embed merken
                if (
                    getattr(chunk, "name", None) == "score_and_rank_videos"
                    and isinstance(out, list)
                    and out
                ):
                    first = out[0]
                    top_video_id = (
                        extract_youtube_id(str(first.get("url", "")))
                        or first.get("video_id")
                    )
            elif getattr(chunk, "content", None):
                content = chunk.content
                if isinstance(content, list):
                    content = "".join(
                        part.get("text", "") if isinstance(part, dict) else str(part)
                        for part in content
                    )
                if content:
                    full_res += str(content)
                    ans_box.markdown(full_res)

        status_box.update(
            label="✨ Recherche abgeschlossen!",
            state="complete",
            expanded=False,
        )

        if not top_video_id:
            top_video_id = extract_youtube_id(full_res)

        if top_video_id:
            st.video(f"https://www.youtube.com/watch?v={top_video_id}")
        else:
            st.info(
                "Kein Video-Link zum Einbetten gefunden – "
                "siehe die Textantwort des Agenten oben."
            )
            show_default_video()
    else:
        show_default_video()


def _running_in_streamlit() -> bool:
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx

        return get_script_run_ctx() is not None
    except Exception:
        return False


if _running_in_streamlit():
    main()
