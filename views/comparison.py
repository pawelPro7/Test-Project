import numpy as np
import pandas as pd
import streamlit as st

from utils.data_loader import load_playermatchstats, aggregate_player, POSITION_LABELS_PL
from utils.styling import page_header, section_divider
from utils.viz import radar_chart_figure, percentile_scale

pms = load_playermatchstats()
if pms.empty:
    st.error("Missing `data/playermatchstats.csv`.")
    st.stop()

page_header(
    eyebrow="Comparison",
    title="Player comparison",
    subtitle="Select 2 to 4 players to compare their profiles on a shared radar chart.",
)

all_players = sorted(pms["playerName"].dropna().unique())
default_sel = all_players[:2] if len(all_players) >= 2 else all_players
selected = st.multiselect("Players to compare (2–4)", all_players, default=default_sel, max_selections=4,
                            key="cmp_players")

if len(selected) < 2:
    st.info("Select at least two players.")
    st.stop()

RADAR_METRICS = {
    "Successful passes": "SUCCESSFUL_PASSES", "Offensive touches": "OFFENSIVE_TOUCHES",
    "Ground duels": "WON_GROUND_DUELS", "Aerial duels": "WON_AERIAL_DUELS",
    "Ball wins": "BALL_WIN_NUMBER", "Packing xG": "PACKING_XG",
    "Shot creating actions": "SHOT_CREATING_ACTIONS", "Bypassed opponents": "BYPASSED_OPPONENTS",
}
RADAR_METRICS = {k: v for k, v in RADAR_METRICS.items() if v in pms.columns}

section_divider("Radar profile (percentile of latest match)")
series = {}
latest_rows = {}
for name in selected:
    rows = pms[pms["playerName"] == name].sort_values("dateTime")
    latest_rows[name] = rows.iloc[-1]
    series[name] = percentile_scale(pms, list(RADAR_METRICS.values()), rows.iloc[-1].to_dict())

fig = radar_chart_figure(list(RADAR_METRICS.keys()), series, height=520, title="Player profile percentile")
st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})
st.caption("Each axis is a percentile (0–100) against all performances in the loaded data — not the raw value.")

section_divider("Numeric summary (sum in data)")
table_rows = []
for name in selected:
    agg = aggregate_player(pms, name)
    latest = latest_rows[name]
    table_rows.append({
        "Player": name,
        "Team": latest.get("squadName"),
        "Position": POSITION_LABELS_PL.get(latest.get("position"), latest.get("position")),
        "Matches": int(agg.get("MATCHES", 0)),
        "Goals": int(agg.get("GOALS", 0)),
        "Assists": int(agg.get("ASSISTS", 0)),
        "Shot xG": round(float(agg.get("SHOT_XG", 0)), 2),
        "Packing xG": round(float(agg.get("PACKING_XG", 0)), 2),
        "Successful passes": int(agg.get("SUCCESSFUL_PASSES", 0)),
        "Pass acc %": round(float(agg.get("pass_accuracy_pct", np.nan)), 1) if pd.notna(agg.get("pass_accuracy_pct", np.nan)) else None,
        "Ball wins": int(agg.get("BALL_WIN_NUMBER", 0)),
        "Bypassed opponents": round(float(agg.get("BYPASSED_OPPONENTS", 0)), 1),
    })
cmp_table = pd.DataFrame(table_rows).set_index("Player").T.astype(str)
st.dataframe(cmp_table, width='stretch')
