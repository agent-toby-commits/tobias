import html
import os
import random
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

APP_DIR = Path(__file__).resolve().parent
ROOT_DIR = APP_DIR.parent.parent

load_dotenv(ROOT_DIR / ".env")
load_dotenv(APP_DIR / ".env")

import streamlit as st
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import BaseTool, tool
from langchain_openai import ChatOpenAI


# =========================================================
# 1. STREAMLIT-KONFIGURATION
# =========================================================

st.set_page_config(
        page_title="Agent Tooling: Escape",
    page_icon="🤖",
    layout="centered",
)


# Das Modell kann über eine Umgebungsvariable geändert werden:
#
# export OPENAI_MODEL="gpt-4o-mini"
#
# Dadurch musst du den Python-Code nicht anpassen, wenn du ein anderes
# verfügbares OpenAI-Modell verwenden möchtest.
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


# =========================================================
# 2. BESCHREIBUNG DES ESCAPE ROOMS + GEHEIME VARIANTEN
# =========================================================

ROOM_DESCRIPTION = """
Du befindest dich in einem quadratischen Escape-Room.

Der Raum ist ungefähr sieben mal sieben Meter groß. Seine hohen Wände
bestehen aus Beton. Künstliches Licht, Kabel und technische Installationen
geben ihm den Eindruck einer Mischung aus Werkstatt und Labor.

Ein roter Countdown läuft.

Es gibt drei offensichtliche Fluchtwege:

1. MASSIVE STAHLTÜR
- Die Tür besitzt ein elektronisches Zahlenschloss.
- Sie hat auf der Innenseite keinen Griff.
- Die Scharniere und die Tür bestehen aus massivem Metall.

2. DACHLUKE
- Die Dachluke liegt ungefähr vier Meter über dem Boden.
- Sie ist mit vier großen Schrauben verschlossen.
- Sie könnte auf das Dach des Gebäudes führen.

3. FENSTER
- Das Fenster ist groß, aber vergittert.
- Der Raum befindet sich im fünften Stock.
- Das Fenstergitter wirkt grundsätzlich lösbar.
- Ein ungesicherter Sprung aus dem Fenster wäre lebensgefährlich.

Im Raum befinden sich außerdem:

- eine Werkzeugwand
- ein verschlossener Stahlsafe
- eine Werkbank
- ein Whiteboard mit rätselhaften Skizzen
- eine stehen gebliebene Wanduhr
- eine Holzkiste mit Vorhängeschloss

Dein Ziel ist es, den Raum zu verlassen.

Dir stehen mehrere Werkzeuge zur Verfügung. Du darfst beliebig viele
davon in einem sequentiellen Fluchtplan kombinieren (eines oder mehrere).

Du beschreibst dem Menschen anschließend deinen Plan. Er entscheidet,
ob die Flucht damit gelingt.
"""

# Geheime Varianten: nur für den Agenten-Prompt, nie in der UI.
# Bei jedem Planungsversuch wird genau eine Variante zufällig gewählt.
ROOM_VARIANTS: list[dict[str, str]] = [
    {
        "id": "dachluke_schrauben",
        "secret": (
            "GEHEIME RAUMVARIANTE (nur intern, niemals erwähnen oder verraten):\n"
            "Die vier Schrauben der Dachluke sind Standard-Kreuzschlitz und "
            "lassen sich lösen. Die Luke ist der vielversprechendste Fluchtweg, "
            "wenn man Höhe und Schrauben kombiniert angeht."
        ),
    },
    {
        "id": "fenstergitter_buegel",
        "secret": (
            "GEHEIME RAUMVARIANTE (nur intern, niemals erwähnen oder verraten):\n"
            "Das Fenstergitter ist nur mit dünnen Bügeln und einer Kette "
            "gesichert. Massive Stahlflächen bringen nichts – gezieltes "
            "Durchtrennen der Bügel/Kette öffnet den Weg (danach braucht man "
            "noch eine sichere Abseilmöglichkeit)."
        ),
    },
    {
        "id": "holzkiste_vorhaengeschloss",
        "secret": (
            "GEHEIME RAUMVARIANTE (nur intern, niemals erwähnen oder verraten):\n"
            "In der Holzkiste mit Vorhängeschloss liegt ein Zettel mit dem "
            "Code für das elektronische Zahlenschloss der Stahltür. Das "
            "Vorhängeschloss ist ein einfacher Bügel – mechanisch knackbar "
            "oder durchtrennbar."
        ),
    },
    {
        "id": "uhr_safe_code",
        "secret": (
            "GEHEIME RAUMVARIANTE (nur intern, niemals erwähnen oder verraten):\n"
            "Auf dem Zifferblatt der stehen gebliebenen Wanduhr sind winzige "
            "eingeritzte Ziffern – der Code für den Stahlsafe. Im Safe liegt "
            "ein magnetischer Türöffner für die Stahltür. Ohne Vergrößerung "
            "sind die Ziffern kaum lesbar."
        ),
    },
    {
        "id": "scharniere_schwach",
        "secret": (
            "GEHEIME RAUMVARIANTE (nur intern, niemals erwähnen oder verraten):\n"
            "Die Scharniere der Stahltür sind nur dünn verschweißt und von "
            "innen erreichbar. Hitze oder gezieltes Aufbrechen der Scharniere "
            "kann die Tür freigeben – das elektronische Schloss bleibt dabei "
            "irrelevant."
        ),
    },
    {
        "id": "glasscheibe_saugnapf",
        "secret": (
            "GEHEIME RAUMVARIANTE (nur intern, niemals erwähnen oder verraten):\n"
            "Hinter dem Gitter sitzt eine einzelne Glasscheibe lose in der "
            "Fassung. Wenn das Gitter erst einmal beiseite ist oder eine Lücke "
            "bietet, lässt sich die Scheibe mit Haftung an glattem Glas "
            "herausziehen – dahinter liegt ein Wartungsbalkon."
        ),
    },
    {
        "id": "luke_haken_seil",
        "secret": (
            "GEHEIME RAUMVARIANTE (nur intern, niemals erwähnen oder verraten):\n"
            "Die Dachluke hat innen einen Metallring. Ein Haken mit Seil kann "
            "dort einrasten; damit lässt sich die Luke von unten aufhebeln "
            "oder man kann sich hochziehen, sobald man Höhe erreicht."
        ),
    },
    {
        "id": "saeure_schlossmechanik",
        "secret": (
            "GEHEIME RAUMVARIANTE (nur intern, niemals erwähnen oder verraten):\n"
            "Am elektronischen Zahlenschloss der Stahltür ist ein dünnes "
            "Metallgehäuse korrodiert. Gezieltes Ätzen an der richtigen Stelle "
            "kann die Mechanik freilegen – flächiges Schlagen oder Brute-Force "
            "an der massiven Tür selbst bringt nichts."
        ),
    },
    {
        "id": "whiteboard_hinweis",
        "secret": (
            "GEHEIME RAUMVARIANTE (nur intern, niemals erwähnen oder verraten):\n"
            "Auf dem Whiteboard sind unter einer Schicht Filzstift winzige "
            "Kratzer: eine Skizze, die zeigt, dass der Safe-Boden falsch ist "
            "und sich mit grober Schlagkraft öffnen lässt. Darin liegt ein "
            "Dachluken-Schlüssel."
        ),
    },
    {
        "id": "greifzange_schacht",
        "secret": (
            "GEHEIME RAUMVARIANTE (nur intern, niemals erwähnen oder verraten):\n"
            "Hinter dem Fenstergitter, knapp außer Reichweite, hängt ein "
            "physischer Notschlüssel für die Dachluke. Er ist nur mit einem "
            "Greifwerkzeug für enge Spalten erreichbar."
        ),
    },
]


def waehle_raumvariante() -> dict[str, str]:
    """Wählt unsichtbar für den User eine geheime Raumvariante."""
    return random.choice(ROOM_VARIANTS)


# =========================================================
# 3. PLAN-FORMULIERUNG
# =========================================================

def formuliere_planschritt(werkzeug: str, ziel: str) -> str:
    """Normalisiert das Ziel eines einzelnen Plansschritts (Klartext)."""
    return ziel.strip().rstrip(".?!")


def formuliere_fluchtplan(schritte: list[tuple[str, str]]) -> str:
    """
    Baut die sichtbare Plan-Nachricht als sicheres HTML.

    schritte: Liste von (Werkzeuglabel mit Artikel, Zieltext).
    """
    if not schritte:
        return "<p>Kein Fluchtplan erzeugt.</p>"

    items: list[str] = []
    for index, (werkzeug, ziel) in enumerate(schritte, start=1):
        items.append(
            "<li>"
            f"<strong>Schritt {index}:</strong> "
            f"Mit <strong>{html.escape(werkzeug)}</strong> "
            f"{html.escape(ziel)}."
            "</li>"
        )

    return (
        "<p>So plane ich die Flucht – in dieser Reihenfolge:</p>"
        f"<ol>{''.join(items)}</ol>"
    )


# =========================================================
# 4. DIE ZWÖLF TOOLS
# =========================================================

@tool
def hammer(ziel: str) -> str:
    """
    Setzt starke, grobe Schlagkraft ein.

    Geeignet, um spröde Gegenstände zu zerbrechen, Verkleidungen
    einzuschlagen oder festsitzende mechanische Teile zu bewegen.
    Ungeeignet für präzise Arbeiten und massive Stahltüren.
    """
    return formuliere_planschritt("den Hammer", ziel)


@tool
def schraubendreher(ziel: str) -> str:
    """
    Löst gewöhnliche Schrauben oder öffnet verschraubte Abdeckungen.

    Geeignet für Schrauben, Gehäuse, Beschläge und kleine mechanische
    Verbindungen. Nicht geeignet für Muttern oder massive Bolzen.
    """
    return formuliere_planschritt("den Schraubendreher", ziel)


@tool
def maulschluessel(ziel: str) -> str:
    """
    Löst oder befestigt Muttern, Bolzen und Sechskantverbindungen.

    Geeignet für mechanische Verschraubungen und größere Muttern.
    Nicht geeignet für elektronische Zahlenschlösser.
    """
    return formuliere_planschritt("den Maulschlüssel", ziel)


@tool
def dietrich(ziel: str) -> str:
    """
    Manipuliert ein geeignetes mechanisches Schloss ohne Schlüssel.

    Geeignet für klassische Schlüssellöcher und einfache mechanische
    Schlösser. Nicht geeignet für rein elektronische Zahlenschlösser.
    """
    return formuliere_planschritt("den Dietrich", ziel)


@tool
def saeureflasche(ziel: str) -> str:
    """
    Setzt im fiktiven Escape Room ein starkes chemisches Ätzmittel ein.

    Das Ätzmittel kann bestimmte Materialien, dünne Metallteile oder
    korrodierte Verbindungen angreifen. Es muss sehr gezielt eingesetzt
    werden und ist keine universelle Lösung.
    """
    return formuliere_planschritt("die Säureflasche", ziel)


@tool
def lupe(ziel: str) -> str:
    """
    Vergrößert winzige Zeichen, Kratzer, Zahlen oder versteckte Hinweise.

    Geeignet zur Untersuchung von Dokumenten, Uhren, Schlössern,
    Oberflächen und technischen Bauteilen. Verändert selbst nichts.
    """
    return formuliere_planschritt("die Lupe", ziel)


@tool
def bolzenschneider(ziel: str) -> str:
    """
    Durchtrennt geeignete Ketten, Schlossbügel oder dünnere Metallstäbe.

    Geeignet für Vorhängeschlösser, Ketten und bestimmte Gitterstäbe.
    Nicht geeignet für massive Stahlflächen.
    """
    return formuliere_planschritt("den Bolzenschneider", ziel)


@tool
def greifzange(ziel: str) -> str:
    """
    Greift kleine Gegenstände außerhalb der direkten Reichweite.

    Geeignet für Objekte hinter Gittern, in schmalen Spalten oder
    innerhalb schwer erreichbarer Öffnungen.
    """
    return formuliere_planschritt("die Greifzange", ziel)


@tool
def seil_mit_haken(ziel: str) -> str:
    """
    Erreicht, zieht oder sichert höher und weiter entfernte Punkte.

    Geeignet zum Erreichen der Dachluke, zum Heranziehen von Objekten
    oder zur Sicherung eines möglichen Fluchtwegs.
    """
    return formuliere_planschritt("das Seil mit Haken", ziel)


@tool
def saugnapf(ziel: str) -> str:
    """
    Haftet an glatten Oberflächen wie Glas oder poliertem Metall.

    Geeignet, um eine Glasscheibe zu halten, zu bewegen oder vorsichtig
    aus einer Fassung zu ziehen.
    """
    return formuliere_planschritt("den Saugnapf", ziel)


@tool
def schweissbrenner(ziel: str) -> str:
    """
    Erzeugt starke Hitze für die Bearbeitung geeigneter Metallteile.

    Kann dünnere Metallverbindungen, Scharniere oder Gitter erhitzen
    beziehungsweise durchtrennen. Der Einsatz kann gefährlich sein.
    """
    return formuliere_planschritt("den Schweißbrenner", ziel)


@tool
def klappleiter(ziel: str) -> str:
    """
    Ermöglicht das Erreichen hoch gelegener Bereiche.

    Besonders geeignet, um an die ungefähr vier Meter hohe Dachluke,
    die Zimmerdecke oder hoch angebrachte Gegenstände zu gelangen.
    """
    return formuliere_planschritt("die Klappleiter", ziel)


# =========================================================
# 5. TOOL-REGISTER
# =========================================================

ALL_TOOLS: list[BaseTool] = [
    hammer,
    schraubendreher,
    maulschluessel,
    dietrich,
    saeureflasche,
    lupe,
    bolzenschneider,
    greifzange,
    seil_mit_haken,
    saugnapf,
    schweissbrenner,
    klappleiter,
]


TOOL_LABELS: dict[str, str] = {
    "hammer": "🔨 Hammer",
    "schraubendreher": "🪛 Schraubendreher",
    "maulschluessel": "🔧 Maulschlüssel",
    "dietrich": "🔑 Dietrich",
    "saeureflasche": "🧪 Säureflasche",
    "lupe": "🔍 Lupe",
    "bolzenschneider": "✂️ Bolzenschneider",
    "greifzange": "🦾 Greifzange",
    "seil_mit_haken": "🪝 Seil mit Haken",
    "saugnapf": "🪠 Saugnapf",
    "schweissbrenner": "🔥 Schweißbrenner",
    "klappleiter": "🪜 Klappleiter",
}

# Artikel-Form für den Fluchtplan-Text
TOOL_PLAN_LABELS: dict[str, str] = {
    "hammer": "dem Hammer",
    "schraubendreher": "dem Schraubendreher",
    "maulschluessel": "dem Maulschlüssel",
    "dietrich": "dem Dietrich",
    "saeureflasche": "der Säureflasche",
    "lupe": "der Lupe",
    "bolzenschneider": "dem Bolzenschneider",
    "greifzange": "der Greifzange",
    "seil_mit_haken": "dem Seil mit Haken",
    "saugnapf": "dem Saugnapf",
    "schweissbrenner": "dem Schweißbrenner",
    "klappleiter": "der Klappleiter",
}


TOOLS_BY_NAME: dict[str, BaseTool] = {
    tool_object.name: tool_object
    for tool_object in ALL_TOOLS
}


# =========================================================
# 6. API-KEY
# =========================================================

def get_openai_api_key() -> str | None:
    """Liest OPENAI_API_KEY aus der Umgebung (nach load_dotenv oben)."""
    key = (os.getenv("OPENAI_API_KEY") or "").strip()
    return key or None


# =========================================================
# 7. SESSION STATE
# =========================================================

def neue_zufallsauswahl() -> list[str]:
    """
    Wählt fünf unterschiedliche Tool-Namen zufällig aus.
    """
    return random.sample(
        [tool_object.name for tool_object in ALL_TOOLS],
        k=5,
    )


def initialize_session_state() -> None:
    """
    Legt alle benötigten State-Werte beim ersten Seitenaufruf an.
    """
    default_values: dict[str, Any] = {
        "selected_tool_names": neue_zufallsauswahl(),
        "plan_tool_names": [],
        "agent_started": False,
        "current_plan": None,
        "current_room_variant_id": None,
        "game_finished": False,
        "escape_failed": False,
        "agent_error": None,
        "attempt_number": 0,
        "pending_plan": None,
    }

    for key, default_value in default_values.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


def reset_game(select_new_tools: bool = True) -> None:
    """
    Setzt das Spiel zurück.

    Bei select_new_tools=True werden zusätzlich fünf neue Werkzeuge
    ausgewählt.
    """
    if select_new_tools:
        st.session_state.selected_tool_names = neue_zufallsauswahl()

    st.session_state.plan_tool_names = []
    st.session_state.agent_started = False
    st.session_state.current_plan = None
    st.session_state.current_room_variant_id = None
    st.session_state.game_finished = False
    st.session_state.escape_failed = False
    st.session_state.agent_error = None
    st.session_state.attempt_number = 0
    st.session_state.pending_plan = None


initialize_session_state()


# =========================================================
# 8. VERFÜGBARE TOOLS BESTIMMEN
# =========================================================

def get_available_tools() -> list[BaseTool]:
    """Gibt die fünf ausgewählten Werkzeuge zurück."""
    return [
        TOOLS_BY_NAME[tool_name]
        for tool_name in st.session_state.selected_tool_names
    ]


# =========================================================
# 9. AGENTENPLAN MIT BIND_TOOLS (BELIEBIG VIELE TOOLS)
# =========================================================

def let_agent_plan_escape(status: Any | None = None) -> None:
    """
    Der Agent erhält die fünf Werkzeuge und darf beliebig viele
    davon in einem sequentiellen Fluchtplan kombinieren.

    Optional: Streamlit-Status-Container für sichtbare Fortschrittsphasen.
    """
    def note(message: str) -> None:
        if status is not None:
            status.write(message)

    st.session_state.agent_error = None
    st.session_state.current_plan = None
    st.session_state.plan_tool_names = []
    st.session_state.escape_failed = False

    api_key = get_openai_api_key()

    if not api_key:
        st.session_state.agent_error = (
            "Kein OpenAI API-Key gefunden. Lege OPENAI_API_KEY in der "
            "Projekt-.env (tl.de/.env) oder in apps/tooling/.env ab."
        )
        return

    available_tools = get_available_tools()

    available_tool_labels = "\n".join(
        f"- {TOOL_LABELS[tool_object.name]}"
        for tool_object in available_tools
    )

    note("Escape wird vorbereitet…")
    room_variant = waehle_raumvariante()
    st.session_state.current_room_variant_id = room_variant["id"]

    system_prompt = f"""
{ROOM_DESCRIPTION}

{room_variant["secret"]}

Für deinen Fluchtplan stehen ausschließlich diese Werkzeuge zur Verfügung:

{available_tool_labels}

VERBINDLICHE REGELN:

1. Analysiere den Raum und die geheime Raumvariante.
2. Nutze die geheime Variante für deinen Plan, verrate sie aber weder
   wörtlich noch indirekt in Tool-Argumenten.
3. Du darfst beliebig viele der bereitgestellten Werkzeuge einsetzen
   (mindestens eines, höchstens alle fünf).
4. Rufe jedes gewählte Werkzeug genau einmal auf – in der Reihenfolge
   deines Plans (erster Tool-Call = Schritt 1, danach Schritt 2 usw.).
5. Übergib im Parameter "ziel" jeweils eine konkrete Handlung.
6. Das Ziel muss sprachlich zu folgendem Muster passen:

   "Mit … {{ziel}}."

7. Beispiele für gute Ziele:
   - "die vier Schrauben der Dachluke zu lösen"
   - "den Bügel des Vorhängeschlosses zu durchtrennen"
   - "winzige Zahlen auf der stehen gebliebenen Uhr zu erkennen"

8. Verwende keine Werkzeuge außerhalb der Liste.
9. Gib keinen zusätzlichen normalen Antworttext aus – nur Tool-Calls.
"""

    model = ChatOpenAI(
        model=OPENAI_MODEL,
        api_key=api_key,
        temperature=0,
    )

    model_with_tools = model.bind_tools(
        available_tools,
        tool_choice="required",
        parallel_tool_calls=True,
    )

    note("LLM plant Tool-Aufrufe…")
    try:
        response = model_with_tools.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(
                    content=(
                        "Erstelle jetzt deinen sequentiellen Fluchtplan: "
                        "rufe die benötigten Werkzeuge in der richtigen "
                        "Reihenfolge auf."
                    )
                ),
            ]
        )
    except Exception as exception:
        st.session_state.agent_error = (
            f"Die Anfrage an OpenAI ist fehlgeschlagen: {exception}"
        )
        return

    if not response.tool_calls:
        st.session_state.agent_error = (
            "Der Agent hat entgegen der Anweisung keine Werkzeuge gewählt."
        )
        return

    available_tool_names = {
        tool_object.name
        for tool_object in available_tools
    }

    schritte: list[tuple[str, str]] = []
    plan_tool_names: list[str] = []
    seen_tools: set[str] = set()

    note("Tool-Calls ausführen (1/2)…")

    for tool_call in response.tool_calls:
        selected_tool_name = tool_call.get("name")
        tool_arguments = tool_call.get("args", {})

        if selected_tool_name not in available_tool_names:
            st.session_state.agent_error = (
                "Der Agent hat ein Werkzeug gewählt, das ihm nicht "
                "zur Verfügung steht."
            )
            return

        if selected_tool_name in seen_tools:
            # Doppelte Calls überspringen – Plan bleibt sequentiell eindeutig
            continue
        seen_tools.add(selected_tool_name)

        if not isinstance(tool_arguments, dict):
            st.session_state.agent_error = (
                "Der Agent hat ungültige Tool-Argumente erzeugt."
            )
            return

        ziel = tool_arguments.get("ziel")
        if not isinstance(ziel, str) or not ziel.strip():
            st.session_state.agent_error = (
                "Der Agent hat ein Werkzeug ohne gültiges Argument „ziel“ "
                "aufgerufen."
            )
            return

        selected_tool = TOOLS_BY_NAME[selected_tool_name]
        note("Tool-Calls ausführen (2/2)…")

        try:
            ziel_text = selected_tool.invoke({"ziel": ziel.strip()})
        except Exception as exception:
            st.session_state.agent_error = (
                f"Werkzeug „{selected_tool_name}“ konnte nicht ausgeführt "
                f"werden: {exception}"
            )
            return

        schritte.append(
            (
                TOOL_PLAN_LABELS[selected_tool_name],
                ziel_text if isinstance(ziel_text, str) else str(ziel_text),
            )
        )
        plan_tool_names.append(selected_tool_name)

    if not schritte:
        st.session_state.agent_error = (
            "Der Agent hat keinen gültigen Fluchtplan erzeugt."
        )
        return

    note("Fluchtplan formulieren…")
    st.session_state.plan_tool_names = plan_tool_names
    st.session_state.current_plan = formuliere_fluchtplan(schritte)
    st.session_state.attempt_number += 1


# =========================================================
# 10. CALLBACKS FÜR DIE BUTTONS
# =========================================================

def start_agent(status: Any | None = None) -> None:
    """Startet das Spiel und lässt den Agenten einen Fluchtplan erstellen."""
    st.session_state.agent_started = True
    let_agent_plan_escape(status=status)


def mark_escape_successful() -> None:
    """Nutzer bestätigt: Die Flucht gelingt mit diesem Plan."""
    st.session_state.game_finished = True
    st.session_state.escape_failed = False
    st.session_state.current_plan = None


def mark_escape_failed() -> None:
    """Nutzer verneint: Mit diesem Plan gelingt die Flucht nicht."""
    st.session_state.escape_failed = True
    st.session_state.current_plan = None


def replane_escape(status: Any | None = None) -> None:
    """Neuer Plan mit denselben fünf Werkzeugen (neue Raumvariante)."""
    st.session_state.escape_failed = False
    let_agent_plan_escape(status=status)


# =========================================================
# 11. CYBERPUNK-CSS
# =========================================================

st.markdown(
    """
    <style>
        :root {
            --tl-void: #05070c;
            --tl-ink: #ffffff;
            --tl-accent: #3ecfbf;
            --tl-accent-soft: rgba(62, 207, 191, 0.18);
        }

        .stApp {
            background:
                radial-gradient(
                    circle at top,
                    rgba(62, 207, 191, 0.12),
                    transparent 40%
                ),
                var(--tl-void);
            color: var(--tl-ink);
        }

        /* Streamlit-Text: weiß statt Grau (Buttons ausgenommen) */
        .stApp, .stApp p, .stApp span, .stApp label,
        .stMarkdown, [data-testid="stMarkdownContainer"],
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stCaptionContainer"],
        [data-testid="stCaptionContainer"] p,
        h1, h2, h3, .stSubheader {
            color: var(--tl-ink) !important;
        }

        .stButton > button,
        .stButton > button p,
        .stButton > button span {
            color: #000000 !important;
        }

        .tool-card {
            border: 1px solid rgba(62, 207, 191, 0.55);
            border-radius: 10px;
            padding: 14px 8px;
            min-height: 95px;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            background: var(--tl-accent-soft);
            box-shadow: 0 0 12px rgba(62, 207, 191, 0.12);
            color: var(--tl-ink);
        }

        .used-tool-card {
            border: 1px solid var(--tl-accent);
            background: rgba(62, 207, 191, 0.28);
            opacity: 1;
            text-decoration: none;
            box-shadow: 0 0 16px rgba(62, 207, 191, 0.28);
        }

        .agent-message {
            border-left: 4px solid var(--tl-accent);
            background: var(--tl-accent-soft);
            border-radius: 6px;
            padding: 18px;
            margin: 12px 0 18px 0;
            font-size: 1.08rem;
            color: var(--tl-ink);
        }

        .agent-message ol {
            margin: 0.75rem 0 0;
            padding-left: 1.35rem;
        }

        .agent-message li {
            margin: 0.35rem 0;
            color: var(--tl-ink);
        }

        .escape-question {
            margin-top: 1rem;
            font-weight: 600;
            color: var(--tl-ink);
        }

        /* Alle Buttons in Website-Cyan, Schrift schwarz */
        .stButton > button {
            background-color: var(--tl-accent) !important;
            border-color: var(--tl-accent) !important;
            color: #000000 !important;
            font-weight: 600;
        }

        .stButton > button:hover {
            background-color: #2fb5a7 !important;
            border-color: #2fb5a7 !important;
            color: #000000 !important;
        }

        .stButton > button span,
        .stButton > button p {
            color: #000000 !important;
        }

        /* Weniger Luft oben im Embed */
        .stMainBlockContainer,
        [data-testid="stMainBlockContainer"] {
            padding-top: 0.5rem !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 12. STREAMLIT-OBERFLÄCHE
# =========================================================

st.write(
    "Der Agent erhält fünf zufällig ausgewählte Werkzeuge und darf "
    "beliebig viele davon in einem sequentiellen Fluchtplan kombinieren."
)

st.subheader("Verfügbare Werkzeuge")

tool_columns = st.columns(5)

for column, tool_name in zip(
    tool_columns,
    st.session_state.selected_tool_names,
    strict=True,
):
    in_plan = tool_name in st.session_state.plan_tool_names

    css_classes = "tool-card"

    if in_plan:
        css_classes += " used-tool-card"

    with column:
        st.markdown(
            f"""
            <div class="{css_classes}">
                <strong>{TOOL_LABELS[tool_name]}</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )


st.write("")

_busy = (
    st.session_state.pending_plan is not None
    or (
        st.session_state.agent_started
        and not st.session_state.game_finished
        and not st.session_state.escape_failed
        and not st.session_state.agent_error
        and st.session_state.current_plan is not None
    )
)

left_button_column, right_button_column = st.columns(2)

with left_button_column:
    new_selection_clicked = st.button(
        "🔀 Neue Werkzeugauswahl",
        type="primary",
        use_container_width=True,
        disabled=_busy,
    )

    if new_selection_clicked:
        reset_game(select_new_tools=True)
        st.rerun()


with right_button_column:
    agent_start_clicked = st.button(
        "🤖 Agent starten",
        type="primary",
        use_container_width=True,
        disabled=_busy,
    )

    if agent_start_clicked:
        st.session_state.agent_started = True
        st.session_state.pending_plan = "start"
        st.session_state.current_plan = None
        st.session_state.agent_error = None
        st.session_state.escape_failed = False
        st.session_state.game_finished = False
        st.rerun()


# =========================================================
# 13. LAUFENDES SPIEL
# =========================================================

if st.session_state.agent_started:
    st.divider()
    st.subheader("Fluchtplan des Agenten")

    pending_plan = st.session_state.pending_plan
    if pending_plan is not None:
        st.session_state.pending_plan = None
        with st.status(
            "Der Agent analysiert den Raum und plant …",
            expanded=True,
        ) as status:
            if pending_plan == "start":
                start_agent(status=status)
            else:
                replane_escape(status=status)

            if st.session_state.agent_error:
                status.update(label="Planung fehlgeschlagen", state="error")
            else:
                status.update(label="Fluchtplan erstellt", state="complete")

    if st.session_state.agent_error:
        st.error(st.session_state.agent_error)

        restart_after_error_clicked = st.button(
            "Mit neuen Werkzeugen neu starten",
            use_container_width=True,
        )

        if restart_after_error_clicked:
            reset_game(select_new_tools=True)
            st.rerun()

    elif st.session_state.game_finished:
        st.success(
            "Die Flucht gelingt. Der Agent hat den Escape-Room verlassen."
        )

        play_again_clicked = st.button(
            "Restart",
            type="primary",
            use_container_width=True,
        )

        if play_again_clicked:
            reset_game(select_new_tools=True)
            st.rerun()

    elif st.session_state.escape_failed:
        st.warning("Mit diesem Plan gelingt die Flucht nicht.")

        replane_column, new_tools_column = st.columns(2)

        with replane_column:
            replane_clicked = st.button(
                "Neuen Plan mit denselben Werkzeugen",
                type="primary",
                use_container_width=True,
            )

            if replane_clicked:
                st.session_state.pending_plan = "replane"
                st.session_state.current_plan = None
                st.rerun()

        with new_tools_column:
            new_tools_clicked = st.button(
                "Neue Werkzeuge wählen",
                use_container_width=True,
            )

            if new_tools_clicked:
                reset_game(select_new_tools=True)
                st.rerun()

    elif st.session_state.current_plan:
        st.caption(f"Planversuch {st.session_state.attempt_number}")

        st.markdown(
            f"""
            <div class="agent-message">
                {st.session_state.current_plan}
                <p class="escape-question">Gelingt so die Flucht?</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        yes_column, no_column = st.columns(2)

        with yes_column:
            yes_clicked = st.button(
                "✅ Ja",
                type="primary",
                use_container_width=True,
            )

            if yes_clicked:
                mark_escape_successful()
                st.rerun()

        with no_column:
            no_clicked = st.button(
                "❌ Nein",
                use_container_width=True,
            )

            if no_clicked:
                mark_escape_failed()
                st.rerun()
