import pandas as pd
import plotly.express as px
import streamlit as st

from utils.data_loader import load_playermatchstats, data_status
from utils.styling import page_header, section_divider, kpi_card, apply_plotly_theme, COLORS

pms = load_playermatchstats()
status = data_status()

page_header(
    eyebrow="Season 25/26 · Analytics dashboard",
    title="League overview",
    subtitle="Statistics, heatmaps and player comparisons based on files in the data/ folder.",
)

pill_defs = [
    ("playermatchstats.csv", status["playermatchstats"]),
    ("physical.csv", status["physical"]),
    ("events.csv", status["events"]),
]
pills_html = ""
for name, s in pill_defs:
    cls = "ok" if s["ok"] else "warn"
    txt = f"{s['rows']} rows" if s["ok"] else "missing file"
    pills_html += f'<span class="data-pill {cls}">● {name} — {txt}</span>'
st.markdown(pills_html, unsafe_allow_html=True)
st.write("")

if pms.empty:
    st.error("`data/playermatchstats.csv` not found. Upload a file with the required structure and refresh the page.")
    st.stop()

if not status["physical"]["ok"] or not status["events"]["ok"]:
    with st.expander("ℹ️ Note on physical.csv / events.csv — assumed data schema", expanded=False):
        st.markdown(
            "The structure of these two files could not be unambiguously confirmed when building the app "
            "(sample inputs were identical to playermatchstats.csv), so the loader assumes a typical schema "
            "for this data class (physical: distance, sprints, speed; events: type, x/y coordinates, xG) and "
            "matches columns flexibly (case-insensitive). Replace the files in `data/` with your full exports — "
            "if column names differ, update the candidate lists in `utils/data_loader.py` (`PHYSICAL_COLUMN_CANDIDATES` / `EVENTS_COLUMN_CANDIDATES`)."
        )

# ---------------------------------------------------------------- KPI
n_matches = pms["matchId"].nunique()
n_players = pms["playerId"].nunique()
n_teams = pms["squadName"].nunique()
total_goals = int(pms["GOALS"].sum())
avg_xg = pms["SHOT_XG"].sum() / max(n_matches, 1)
pass_acc = pms["pass_accuracy_pct"].mean() if "pass_accuracy_pct" in pms.columns else float("nan")

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.markdown(kpi_card("Matches in data", f"{n_matches}"), unsafe_allow_html=True)
with k2:
    st.markdown(kpi_card("Players", f"{n_players}"), unsafe_allow_html=True)
with k3:
    st.markdown(kpi_card("Teams", f"{n_teams}"), unsafe_allow_html=True)
with k4:
    st.markdown(kpi_card("Total goals", f"{total_goals}", f"{avg_xg:.2f} xG / match"), unsafe_allow_html=True)
with k5:
    st.markdown(kpi_card("Pass accuracy", f"{pass_acc:.0f}%" if pd.notna(pass_acc) else "—"), unsafe_allow_html=True)

st.write("")
section_divider("Stat leaders")

lead_col1, lead_col2, lead_col3 = st.columns(3)

with lead_col1:
    top_scorers = (pms.groupby("playerName", as_index=False)["GOALS"].sum()
                   .query("GOALS > 0").sort_values("GOALS", ascending=False).head(8))
    if not top_scorers.empty:
        fig = px.bar(top_scorers.sort_values("GOALS"), x="GOALS", y="playerName", orientation="h",
                      title="Top scorers", text="GOALS")
        fig.update_traces(marker_color=COLORS["accent"], textposition="outside", cliponaxis=False)
        fig.update_layout(yaxis_title="", xaxis_title="")
        apply_plotly_theme(fig, height=320, show_legend=False)
        st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})
    else:
        st.info("No goals recorded in the data.")

with lead_col2:
    top_assists = (pms.groupby("playerName", as_index=False)["ASSISTS"].sum()
                   .query("ASSISTS > 0").sort_values("ASSISTS", ascending=False).head(8))
    if not top_assists.empty:
        fig = px.bar(top_assists.sort_values("ASSISTS"), x="ASSISTS", y="playerName", orientation="h",
                      title="Most assists", text="ASSISTS")
        fig.update_traces(marker_color=COLORS["accent_3"], textposition="outside", cliponaxis=False)
        fig.update_layout(yaxis_title="", xaxis_title="")
        apply_plotly_theme(fig, height=320, show_legend=False)
        st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})
    else:
        st.info("No assists recorded in the data.")

with lead_col3:
    top_packing = (pms.groupby("playerName", as_index=False)["PACKING_XG"].sum()
                   .sort_values("PACKING_XG", ascending=False).head(8))
    if not top_packing.empty and top_packing["PACKING_XG"].sum() > 0:
        fig = px.bar(top_packing.sort_values("PACKING_XG"), x="PACKING_XG", y="playerName", orientation="h",
                      title="Packing xG (total)", text=top_packing.sort_values("PACKING_XG")["PACKING_XG"].round(2))
        fig.update_traces(marker_color=COLORS["accent_4"], textposition="outside", cliponaxis=False)
        fig.update_layout(yaxis_title="", xaxis_title="")
        apply_plotly_theme(fig, height=320, show_legend=False)
        st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})
    else:
        st.info("No Packing xG data.")

section_divider("Recent matches")

match_team_goals = pms.groupby(["matchId", "dateTime", "competitionName", "squadName"], as_index=False)["GOALS"].sum()
rows = []
for match_id, g in match_team_goals.groupby("matchId"):
    g = g.sort_values("squadName")
    dt = g["dateTime"].iloc[0]
    comp = g["competitionName"].iloc[0]
    if len(g) >= 2:
        a, b = g.iloc[0], g.iloc[1]
        result = f"{a['squadName']}  {int(a['GOALS'])} : {int(b['GOALS'])}  {b['squadName']}"
    else:
        a = g.iloc[0]
        opp_goals = pms.loc[pms["matchId"] == match_id, "OPPONENT_GOALS"]
        opp_txt = f"{int(opp_goals.iloc[0])}" if not opp_goals.empty else "?"
        result = f"{a['squadName']} {int(a['GOALS'])} : {opp_txt} (opponent outside the dataset)"
    rows.append({"Date": dt, "Competition": comp, "Result": result})

matches_table = pd.DataFrame(rows).sort_values("Date", ascending=False)
matches_table["Date"] = pd.to_datetime(matches_table["Date"]).dt.strftime("%Y-%m-%d %H:%M")
st.dataframe(matches_table, width='stretch', hide_index=True)

st.caption(
    "Tip: the **Player** and **Team** pages in the left menu have their own selectors, "
    "and the **Heatmaps** and **Comparison** pages allow comparing multiple players at once."
)
