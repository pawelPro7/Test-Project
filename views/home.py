import pandas as pd
import plotly.express as px
import streamlit as st

from utils.data_loader import (
    load_playermatchstats, load_physical, data_status, resolve_columns, PHYSICAL_COLUMN_CANDIDATES,
)
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
n_players_with_minutes = (
    pms.loc[pms["PLAYDURATION"] > 0, "playerId"].nunique()
    if "PLAYDURATION" in pms.columns else pms["playerId"].nunique()
)
n_teams = pms["squadId"].nunique() if "squadId" in pms.columns else pms["squadName"].nunique()
total_goals = int(pms["GOALS"].sum())
total_shots = int(pms["SHOT_AT_GOAL_NUMBER"].sum()) if "SHOT_AT_GOAL_NUMBER" in pms.columns else 0
goals_per_match = total_goals / max(n_matches, 1)
shot_conversion = (total_goals / total_shots * 100) if total_shots > 0 else float("nan")

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.markdown(kpi_card("Matches", f"{n_matches}"), unsafe_allow_html=True)
with k2:
    st.markdown(kpi_card("Players with minutes", f"{n_players_with_minutes}"), unsafe_allow_html=True)
with k3:
    st.markdown(kpi_card("Teams", f"{n_teams}"), unsafe_allow_html=True)
with k4:
    st.markdown(kpi_card("Goals", f"{total_goals}", f"{goals_per_match:.2f} goals / match"), unsafe_allow_html=True)
with k5:
    st.markdown(
        kpi_card("Shot conversion", f"{shot_conversion:.1f}%" if pd.notna(shot_conversion) else "—",
                  f"{total_goals} goals / {total_shots} shots"),
        unsafe_allow_html=True,
    )

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
    top_shot_xg = (pms.groupby("playerName", as_index=False)["SHOT_XG"].sum()
                   .sort_values("SHOT_XG", ascending=False).head(8))
    if not top_shot_xg.empty and top_shot_xg["SHOT_XG"].sum() > 0:
        fig = px.bar(top_shot_xg.sort_values("SHOT_XG"), x="SHOT_XG", y="playerName", orientation="h",
                      title="Most Shot xG", text=top_shot_xg.sort_values("SHOT_XG")["SHOT_XG"].round(2))
        fig.update_traces(marker_color=COLORS["accent_4"], textposition="outside", cliponaxis=False)
        fig.update_layout(yaxis_title="", xaxis_title="")
        apply_plotly_theme(fig, height=320, show_legend=False)
        st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})
    else:
        st.info("No Shot xG data.")

# ---------------------------------------------------------------- League profile
section_divider("League profile")
st.caption(
    "League-wide rates computed from totals (not averaged per player), so a player with 100 shots "
    "counts as much as one with a single shot. Home/away win rates aren't shown because the data has "
    "no reliable home/away indicator for each match."
)


def _fmt(value, decimals=1, suffix=""):
    return f"{value:.{decimals}f}{suffix}" if pd.notna(value) else "—"


total_90s = pms["PLAYDURATION"].sum() / 5400 if "PLAYDURATION" in pms.columns else float("nan")
xg_per_match = pms["SHOT_XG"].sum() / max(n_matches, 1) if "SHOT_XG" in pms.columns else float("nan")

if {"WON_AERIAL_DUELS", "LOST_AERIAL_DUELS"}.issubset(pms.columns):
    won_aer, lost_aer = pms["WON_AERIAL_DUELS"].sum(), pms["LOST_AERIAL_DUELS"].sum()
    aerial_pct = won_aer / (won_aer + lost_aer) * 100 if (won_aer + lost_aer) > 0 else float("nan")
else:
    aerial_pct = float("nan")

pressures_per90 = (pms["NUMBER_OF_PRESSURES_EVENT"].sum() / total_90s
                    if "NUMBER_OF_PRESSURES_EVENT" in pms.columns and total_90s > 0 else float("nan"))
pxt_pro_per90 = (pms["PXT_PASS_PRO"].sum() / total_90s
                  if "PXT_PASS_PRO" in pms.columns and total_90s > 0 else float("nan"))
ball_loss_per90 = (pms["BALL_LOSS_NUMBER"].sum() / total_90s
                    if "BALL_LOSS_NUMBER" in pms.columns and total_90s > 0 else float("nan"))

hi_per90 = float("nan")
physical = load_physical()
if not physical.empty:
    phys_colmap = resolve_columns(physical, PHYSICAL_COLUMN_CANDIDATES)
    hi_col, min_col = phys_colmap.get("highIntensityActions"), phys_colmap.get("minutesPlayed")
    if hi_col and min_col:
        total_minutes = physical[min_col].sum()
        if total_minutes > 0:
            hi_per90 = physical[hi_col].sum() / (total_minutes / 90)

p1, p2, p3, p4 = st.columns(4)
with p1:
    st.markdown(kpi_card("Goals / match", _fmt(goals_per_match, 2)), unsafe_allow_html=True)
with p2:
    st.markdown(kpi_card("xG / match", _fmt(xg_per_match, 2)), unsafe_allow_html=True)
with p3:
    st.markdown(kpi_card("Shot conversion", _fmt(shot_conversion, 1, "%")), unsafe_allow_html=True)
with p4:
    st.markdown(kpi_card("Aerial-duel success", _fmt(aerial_pct, 1, "%")), unsafe_allow_html=True)

p5, p6, p7, p8 = st.columns(4)
with p5:
    st.markdown(kpi_card("Pressures / 90", _fmt(pressures_per90, 1)), unsafe_allow_html=True)
with p6:
    st.markdown(
        kpi_card("High-intensity actions / 90", _fmt(hi_per90, 1),
                  "from physical.csv" if pd.notna(hi_per90) else "physical.csv has no matching columns"),
        unsafe_allow_html=True,
    )
with p7:
    st.markdown(kpi_card("Progressive passing value", _fmt(pxt_pro_per90, 3), "PXT_PASS_PRO / 90"),
                unsafe_allow_html=True)
with p8:
    st.markdown(kpi_card("Ball losses / 90", _fmt(ball_loss_per90, 1)), unsafe_allow_html=True)

st.caption(
    "Tip: the **Player** and **Team** pages in the left menu have their own selectors, "
    "and the **Heatmaps** and **Comparison** pages allow comparing multiple players at once."
)
