import streamlit as st

from utils.styling import inject_global_css, COLORS

st.set_page_config(
    page_title="Analiza Meczowa",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_global_css()

with st.sidebar:
    st.markdown(f"""
    <div style="padding: 6px 0 14px 0;">
        <div style="font-family:'Oswald',sans-serif; font-size:1.35rem; letter-spacing:0.03em; color:{COLORS['text']};">
            ⚽ ANALIZA MECZOWA
        </div>
        <div style="color:{COLORS['text_muted']}; font-size:0.78rem; margin-top:2px;">
            playermatchstats · physical · events
        </div>
    </div>
    """, unsafe_allow_html=True)

home = st.Page("views/home.py", title="Przegląd", icon="🏠", default=True)
player = st.Page("views/player.py", title="Zawodnik", icon="👤")
team = st.Page("views/team.py", title="Drużyna", icon="🛡️")
heatmaps = st.Page("views/heatmaps.py", title="Mapy cieplne", icon="🔥")
comparison = st.Page("views/comparison.py", title="Porównanie", icon="⚔️")

pg = st.navigation({"Menu": [home, player, team, heatmaps, comparison]})

with st.sidebar:
    st.markdown("---")
    st.caption("Dane wczytywane z folderu `data/`. Podmień pliki CSV własnymi eksportami i odśwież stronę.")

pg.run()
