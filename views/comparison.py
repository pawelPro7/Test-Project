import numpy as np
import pandas as pd
import streamlit as st

from utils.data_loader import load_playermatchstats, aggregate_player, POSITION_LABELS_PL
from utils.styling import page_header, section_divider
from utils.viz import radar_chart_figure, percentile_scale

pms = load_playermatchstats()
if pms.empty:
    st.error("Brak `data/playermatchstats.csv`.")
    st.stop()

page_header(
    eyebrow="Zestawienie",
    title="Porównanie zawodników",
    subtitle="Wybierz od 2 do 4 zawodników, aby zestawić ich profile na wspólnym wykresie radarowym.",
)

all_players = sorted(pms["playerName"].dropna().unique())
default_sel = all_players[:2] if len(all_players) >= 2 else all_players
selected = st.multiselect("Zawodnicy do porównania (2–4)", all_players, default=default_sel, max_selections=4,
                            key="cmp_players")

if len(selected) < 2:
    st.info("Wybierz co najmniej dwóch zawodników.")
    st.stop()

RADAR_METRICS = {
    "Podania celne": "SUCCESSFUL_PASSES", "Dotkn. ofensywne": "OFFENSIVE_TOUCHES",
    "Pojedynki (grunt)": "WON_GROUND_DUELS", "Pojedynki (powietrze)": "WON_AERIAL_DUELS",
    "Odzyskane piłki": "BALL_WIN_NUMBER", "Packing xG": "PACKING_XG",
    "Akcje bramkowe": "SHOT_CREATING_ACTIONS", "Ominięci rywale": "BYPASSED_OPPONENTS",
}
RADAR_METRICS = {k: v for k, v in RADAR_METRICS.items() if v in pms.columns}

section_divider("Profil radarowy (percentyl najnowszego meczu)")
series = {}
latest_rows = {}
for name in selected:
    rows = pms[pms["playerName"] == name].sort_values("dateTime")
    latest_rows[name] = rows.iloc[-1]
    series[name] = percentile_scale(pms, list(RADAR_METRICS.values()), rows.iloc[-1].to_dict())

fig = radar_chart_figure(list(RADAR_METRICS.keys()), series, height=520)
st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})
st.caption("Każda oś to percentyl (0–100) na tle wszystkich występów w załadowanych danych — nie surowa wartość.")

section_divider("Zestawienie liczb (suma w danych)")
table_rows = []
for name in selected:
    agg = aggregate_player(pms, name)
    latest = latest_rows[name]
    table_rows.append({
        "Zawodnik": name,
        "Drużyna": latest.get("squadName"),
        "Pozycja": POSITION_LABELS_PL.get(latest.get("position"), latest.get("position")),
        "Mecze": int(agg.get("MECZE", 0)),
        "Gole": int(agg.get("GOALS", 0)),
        "Asysty": int(agg.get("ASSISTS", 0)),
        "Shot xG": round(float(agg.get("SHOT_XG", 0)), 2),
        "Packing xG": round(float(agg.get("PACKING_XG", 0)), 2),
        "Podania celne": int(agg.get("SUCCESSFUL_PASSES", 0)),
        "Skut. podań %": round(float(agg.get("pass_accuracy_pct", np.nan)), 1) if pd.notna(agg.get("pass_accuracy_pct", np.nan)) else None,
        "Odzyskane piłki": int(agg.get("BALL_WIN_NUMBER", 0)),
        "Ominięci rywale": round(float(agg.get("BYPASSED_OPPONENTS", 0)), 1),
    })
cmp_table = pd.DataFrame(table_rows).set_index("Zawodnik").T.astype(str)
st.dataframe(cmp_table, width='stretch')
