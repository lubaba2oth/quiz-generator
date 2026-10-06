import json
import os
import time

import streamlit as st
from google import genai
from google.genai import types

BEVORZUGT = "gemini-3.8-flash"  # erstes Modell, das probiert wird
AUSSCHLUSS = ("image", "tts", "live", "audio", "embedding", "native", "robotics")
MAX_ZEICHEN = 5000  # Schutz vor Missbrauch und hohen Kosten
MAX_ANFRAGEN = 10  # pro Sitzung

PROMPT = """Du bist ein Lehrer. Erstelle {n} Quizfragen auf Deutsch, ausschließlich auf Basis des folgenden Textes. Erfinde nichts dazu.
Antworte NUR mit JSON in genau diesem Format:
{{"fragen": [{{"frage": "...", "antworten": ["A", "B", "C", "D"], "richtig": 0, "erklaerung": "..."}}]}}
"richtig" ist der Index (0 bis 3) der richtigen Antwort.

Text:
{text}"""


def hole_api_key() -> str | None:
    """Key aus Streamlit-Secrets (Cloud) oder Umgebungsvariable (lokal)."""
    try:
        return st.secrets["GEMINI_API_KEY"]
    except Exception:
        return os.environ.get("GEMINI_API_KEY")


@st.cache_resource(show_spinner=False)
def finde_modelle(_client) -> list[str]:
    """Bevorzugtes Modell zuerst, danach andere Flash-Modelle als Ersatz."""
    modelle = [BEVORZUGT]
    try:
        for m in _client.models.list():
            name = m.name.replace("models/", "")
            if "flash" in name and name not in modelle and not any(x in name for x in AUSSCHLUSS):
                modelle.append(name)
    except Exception:
        pass  # ohne Liste bleibt es beim bevorzugten Modell
    return modelle[:4]


def ist_gueltig(frage: dict) -> bool:
    """Prüft, ob eine Frage alle nötigen Felder hat."""
    try:
        return (
            isinstance(frage["frage"], str)
            and len(frage["antworten"]) == 4
            and frage["richtig"] in (0, 1, 2, 3)
            and isinstance(frage["erklaerung"], str)
        )
    except (KeyError, TypeError):
        return False


def generiere_fragen(client, text: str, n: int, runden: int = 2) -> list[dict]:
    """Probiert mehrere Modelle durch, falls eines überlastet oder nicht verfügbar ist."""
    letzter_fehler = ""
    for runde in range(runden):
        for modell in finde_modelle(client):
            try:
                antwort = client.models.generate_content(
                    model=modell,
                    contents=PROMPT.format(n=n, text=text),
                    config={"response_mime_type": "application/json"},
                )
                daten = json.loads(antwort.text)
                fragen = [f for f in daten["fragen"] if ist_gueltig(f)]
                if fragen:
                    st.session_state.modell = modell
                    return fragen
                letzter_fehler = f"{modell}: keine gültigen Fragen"
            except (json.JSONDecodeError, KeyError, TypeError):
                letzter_fehler = f"{modell}: ungültiges JSON"
            except Exception as e:  # 503, 429, 404 usw.: nächstes Modell probieren
                letzter_fehler = f"{modell}: {str(e)[:150]}"
        if runde < runden - 1:
            time.sleep(3)  # kurz warten, dann alle Modelle nochmal
    st.error(
        "Es hat mit keinem Modell geklappt, vermutlich ist Google gerade überlastet. "
        f"Bitte versuch es in ein paar Minuten nochmal. Letzter Fehler: {letzter_fehler}"
    )
    return []


st.title("Quiz- und Lernkarten-Generator")
st.caption(
    "Hinweis: Der eingegebene Text wird zur Verarbeitung an die Google Gemini API gesendet. "
    "Bitte keine vertraulichen oder personenbezogenen Daten eingeben."
)

api_key = hole_api_key()
if not api_key:
    st.error("Kein API-Key gefunden. Setze GEMINI_API_KEY (siehe README).")
    st.stop()
client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(timeout=30_000),  # 30 Sekunden pro Anfrage
)

text = st.text_area("Vorlesungstext einfügen", height=200, max_chars=MAX_ZEICHEN)
anzahl = st.slider("Anzahl Fragen", 3, 10, 5)

if "anfragen" not in st.session_state:
    st.session_state.anfragen = 0

if st.button("Quiz erzeugen"):
    if len(text.strip()) < 200:
        st.warning("Bitte füge einen längeren Text ein (mindestens ca. 200 Zeichen).")
    elif st.session_state.anfragen >= MAX_ANFRAGEN:
        st.warning("Du hast das Limit für diese Sitzung erreicht. Lade die Seite neu.")
    else:
        st.session_state.anfragen += 1
        with st.spinner("Gemini erstellt Fragen ..."):
            st.session_state.fragen = generiere_fragen(client, text, anzahl)
        st.session_state.karte = 0
        st.session_state.umgedreht = False
        st.session_state.ausgewertet = False

fragen = st.session_state.get("fragen", [])

if fragen:
    st.caption(f"Erstellt mit: {st.session_state.get('modell', 'unbekannt')}")
    tab_quiz, tab_karten = st.tabs(["Quiz", "Lernkarten"])

    with tab_quiz:
        auswahl = []
        for i, f in enumerate(fragen):
            auswahl.append(
                st.radio(f"{i + 1}. {f['frage']}", f["antworten"], index=None, key=f"q{i}")
            )

        if st.button("Auswerten"):
            st.session_state.ausgewertet = True

        if st.session_state.get("ausgewertet"):
            punkte = 0
            for i, f in enumerate(fragen):
                richtig = f["antworten"][f["richtig"]]
                if auswahl[i] == richtig:
                    punkte += 1
                    st.success(f"Frage {i + 1}: richtig. {f['erklaerung']}")
                else:
                    st.error(f"Frage {i + 1}: falsch. Richtig wäre: {richtig}. {f['erklaerung']}")
            st.subheader(f"Ergebnis: {punkte} von {len(fragen)} Punkten")

    with tab_karten:
        i = st.session_state.karte
        f = fragen[i]
        st.caption(f"Karte {i + 1} von {len(fragen)}")
        if st.session_state.umgedreht:
            st.info(f"{f['antworten'][f['richtig']]}\n\n{f['erklaerung']}")
        else:
            st.info(f["frage"])

        col1, col2 = st.columns(2)
        if col1.button("Umdrehen"):
            st.session_state.umgedreht = not st.session_state.umgedreht
            st.rerun()
        if col2.button("Nächste Karte"):
            st.session_state.karte = (i + 1) % len(fragen)
            st.session_state.umgedreht = False
            st.rerun()