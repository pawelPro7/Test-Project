import streamlit as st

from utils.styling import inject_global_css, COLORS

st.set_page_config(
    page_title="Match Analysis",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_global_css()

with st.sidebar:
    st.markdown(f"""
    <div style="padding: 6px 0 14px 0;">
        <div style="font-family:'Oswald',sans-serif; font-size:1.35rem; letter-spacing:0.03em; color:{COLORS['text']};">
            ⚽ MATCH ANALYSIS
        </div>
        <div style="color:{COLORS['text_muted']}; font-size:0.78rem; margin-top:2px;">
            playermatchstats · physical · events
        </div>
    </div>
    """, unsafe_allow_html=True)

home = st.Page("views/home.py", title="Overview", icon="🏠", default=True)
player = st.Page("views/player.py", title="Players", icon="👤")
team = st.Page("views/team.py", title="Teams", icon="🛡️")
heatmaps = st.Page("views/heatmaps.py", title="Heatmaps", icon="🔥")
comparison = st.Page("views/comparison.py", title="Players Comparison", icon="⚔️")

pg = st.navigation({"Menu": [home, player, team, heatmaps, comparison]})

prev_page_title = st.session_state.get("_current_page_title")
st.session_state["_current_page_title"] = pg.title
st.session_state["_navigated_to_new_page"] = prev_page_title != pg.title

pg.run()
