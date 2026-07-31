import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from utils.data_loader import (
    load_playermatchstats, load_physical, get_teams, get_players, aggregate_player,
    zone_grid_from_marginals, resolve_columns, PHYSICAL_COLUMN_CANDIDATES,
    METRIC_LABELS, POSITION_LABELS_PL, ZONE_ORDER, ZONE_LABELS_PL, LANE_ORDER, LANE_LABELS_PL,
)
from utils.styling import page_header, section_divider, kpi_card, apply_plotly_theme, COLORS
from utils.viz import zone_heatmap_figure, radar_chart_figure, percentile_scale

pms = load_playermatchstats()
if pms.empty:
    st.error("Missing `data/playermatchstats.csv`.")
    st.stop()

page_header(
    eyebrow="Directory",
    title="Player",
    subtitle="Select a team and player to view their profile, form and activity zones on the pitch.",
)

sel_col1, sel_col2 = st.columns([1, 2])
teams = ["All teams"] + get_teams(pms)
if "sel_team" not in st.session_state or st.session_state.sel_team not in teams:
    st.session_state.sel_team = "All teams"
with sel_col1:
    team_choice = st.selectbox("Team", teams, key="sel_team")

players = get_players(pms, team_choice)
if not players:
    st.warning("No players for the selected team.")
    st.stop()
if "sel_player" not in st.session_state or st.session_state.sel_player not in players:
    st.session_state.sel_player = players[0]
with sel_col2:
    player_choice = st.selectbox("Player", players, key="sel_player")

player_rows = (
    pms[pms["playerName"] == player_choice]
    .sort_values("dateTime")
    .reset_index(drop=True)
)

# wybór meczu
match_options = ["All matches"] + [
    pd.to_datetime(d).strftime("%Y-%m-%d")
    for d in player_rows["dateTime"]
]

selected_match = st.selectbox(
    "Match",
    options=match_options,
    index=len(match_options) - 1,  # default to latest match
    key="sel_match",
)

if selected_match == "All matches":
    selected_rows = player_rows
    latest = player_rows.iloc[-1]
else:
    selected_rows = player_rows[
        pd.to_datetime(player_rows["dateTime"]).dt.strftime("%Y-%m-%d")
        == selected_match
    ]
    latest = selected_rows.iloc[0]

is_gk = str(latest.get("position")) == "GOALKEEPER"

pos_label = POSITION_LABELS_PL.get(latest.get("position"), latest.get("position"))
age = int(latest["age"]) if "age" in latest and pd.notna(latest["age"]) else None
foot = {"LEFT": "Left", "RIGHT": "Right"}.get(latest.get("leg"), latest.get("leg", "—"))

st.markdown(f"""
<div class="player-card">
  <div class="name">{latest['playerName']}</div>
  <div class="meta">{latest['squadName']} &nbsp;·&nbsp; {pos_label} &nbsp;·&nbsp; {latest.get('playerCountry','—')}</div>
  <div style="margin-top:12px;">
  <span class="tag">Age: {age if age is not None else '—'}</span>
  <span class="tag">Foot: {foot}</span>
  <span class="tag">Matches in data: {len(player_rows)}</span>
  <span class="tag">Last match: {pd.to_datetime(latest['dateTime']).strftime('%Y-%m-%d')}</span>
  </div>
</div>
""", unsafe_allow_html=True)

st.write("")
if selected_match == "Wszystkie mecze":
    agg = aggregate_player(pms, player_choice)
else:
    agg = aggregate_player(selected_rows, player_choice)

if not is_gk:
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    with k1:
        st.markdown(kpi_card("Goals", f"{int(agg.get('GOALS', 0))}"), unsafe_allow_html=True)
    with k2:
        st.markdown(kpi_card("Assists", f"{int(agg.get('ASSISTS', 0))}"), unsafe_allow_html=True)
    with k3:
        st.markdown(kpi_card("Shots", f"{int(agg.get('SHOT_AT_GOAL_NUMBER', 0))}"), unsafe_allow_html=True)
    with k4:
        st.markdown(kpi_card("Shot xG", f"{agg.get('SHOT_XG', 0):.2f}"), unsafe_allow_html=True)
    with k5:
        st.markdown(kpi_card("Packing xG", f"{agg.get('PACKING_XG', 0):.2f}"), unsafe_allow_html=True)
    with k6:
        pa = agg.get("pass_accuracy_pct", np.nan)
        st.markdown(kpi_card("Pass acc", f"{pa:.0f}%" if pd.notna(pa) else "—"), unsafe_allow_html=True)
else:
    gk_rows = player_rows if selected_match == "Wszystkie mecze" else selected_rows
    saves = gk_rows["SHOT_AT_GOAL_NUMBER_SAVED"].sum() if "SHOT_AT_GOAL_NUMBER_SAVED" in gk_rows else 0
    conceded = gk_rows["CONCEDED_GOALS"].sum() if "CONCEDED_GOALS" in gk_rows else 0
    claims = gk_rows["claims"].sum() if "claims" in gk_rows else 0
    catches = gk_rows["gk_catches"].sum() if "gk_catches" in gk_rows else 0
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.markdown(kpi_card("Goals conceded", f"{int(conceded)}"), unsafe_allow_html=True)
    with k2:
        st.markdown(kpi_card("Saves", f"{int(saves)}"), unsafe_allow_html=True)
    with k3:
        st.markdown(kpi_card("Claims", f"{int(claims)}"), unsafe_allow_html=True)
    with k4:
        st.markdown(kpi_card("Catches", f"{int(catches)}"), unsafe_allow_html=True)
    with k5:
        pa = agg.get("pass_accuracy_pct", np.nan)
        st.markdown(kpi_card("Pass acc", f"{pa:.0f}%" if pd.notna(pa) else "—"), unsafe_allow_html=True)

st.write("")
col_left, col_right = st.columns([1, 1])

with col_left:
    section_divider("Profile vs dataset")
    if is_gk:
        radar_cols = {"Successful passes": "SUCCESSFUL_PASSES", "Defensive touches": "DEFENSIVE_TOUCHES",
                      "Claims": "claims", "Catches": "gk_catches",
                      "Saves": "SHOT_AT_GOAL_NUMBER_SAVED", "Defensive PXT": "DEF_PXT_BALL_WIN"}
    else:
        radar_cols = {"Successful passes": "SUCCESSFUL_PASSES", "Offensive touches": "OFFENSIVE_TOUCHES",
                      "Ground duels": "WON_GROUND_DUELS", "Ball wins": "BALL_WIN_NUMBER",
                      "Packing xG": "PACKING_XG", "Shot creating actions": "SHOT_CREATING_ACTIONS"}
    radar_cols = {k: v for k, v in radar_cols.items() if v in pms.columns}
    if radar_cols:
        values = percentile_scale(pms, list(radar_cols.values()), latest.to_dict())
        fig = radar_chart_figure(list(radar_cols.keys()), {player_choice: values}, height=380)
        st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})
        st.caption("Percentile (0–100) of the selected match against all performances in the loaded data.")
    else:
        st.info("Not enough data to build a profile.")

with col_right:
    section_divider("Activity zones (sum of touches)")
    pitch_cols = [f"OFFENSIVE_TOUCHES_IN_PITCH_POSITION_{z}" for z in ZONE_ORDER]
    lane_cols = [f"OFFENSIVE_TOUCHES_IN_LANE_{l}" for l in LANE_ORDER]
    if all(c in player_rows.columns for c in pitch_cols + lane_cols):
        if selected_match == "All matches":
            pitch_counts = player_rows[pitch_cols].sum().tolist()
            lane_counts = player_rows[lane_cols].sum().tolist()
        else:
            pitch_counts = latest[pitch_cols].tolist()
            lane_counts = latest[lane_cols].tolist()
        grid = zone_grid_from_marginals(pitch_counts, lane_counts)
        fig = zone_heatmap_figure(grid, [ZONE_LABELS_PL[z] for z in ZONE_ORDER],
                                    [LANE_LABELS_PL[l] for l in LANE_ORDER], height=380)
        st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})
        st.caption("Approximation based on independent marginal distributions (zone × corridor) — see Heatmaps page.")
    else:
        st.info("No zone columns in the data.")

if len(player_rows) > 1:
    section_divider("Forma w kolejnych meczach")
    metric_label = st.selectbox("Metryka", list(METRIC_LABELS.keys()), index=0, key="player_trend_metric")
    metric_col = METRIC_LABELS[metric_label]
    if metric_col in player_rows.columns:
        trend = player_rows[["dateTime", "matchDayIndex", metric_col]].copy()
        trend["mecz"] = "Kolejka " + trend["matchDayIndex"].astype(str)
        fig = px.line(trend, x="dateTime", y=metric_col, markers=True, hover_data=["mecz"])
        fig.update_traces(line_color=COLORS["accent"], marker=dict(size=9, color=COLORS["accent"]))
        fig.update_layout(xaxis_title="", yaxis_title=metric_label)
        apply_plotly_theme(fig, height=320, show_legend=False)
        st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})

# ---------------------------------------------------------------- Fizyczność
physical = load_physical()
if not physical.empty:
    colmap = resolve_columns(physical, PHYSICAL_COLUMN_CANDIDATES)
    name_col = colmap.get("playerName")
    if name_col and player_choice in physical[name_col].values:
        section_divider("Physicality (physical.csv)")
        p_rows = physical[physical[name_col] == player_choice]

        def avg_of(key, decimals=0):
            c = colmap.get(key)
            if not c or c not in p_rows.columns:
                return None
            return round(float(p_rows[c].mean()), decimals)

        f1, f2, f3, f4 = st.columns(4)
        dist = avg_of("totalDistanceM")
        hsr = avg_of("hsrDistanceM")
        sprints = avg_of("numSprints")
        topspeed = avg_of("topSpeedKmh", 1)
        with f1:
            st.markdown(kpi_card("Avg distance / match", f"{dist:,.0f} m" if dist is not None else "—"), unsafe_allow_html=True)
        with f2:
            st.markdown(kpi_card("Avg HSR distance", f"{hsr:,.0f} m" if hsr is not None else "—"), unsafe_allow_html=True)
        with f3:
            st.markdown(kpi_card("Avg sprints", f"{sprints:,.0f}" if sprints is not None else "—"), unsafe_allow_html=True)
        with f4:
            st.markdown(kpi_card("Top speed", f"{topspeed} km/h" if topspeed is not None else "—"), unsafe_allow_html=True)
    else:
        st.caption("No physical data for this player in `physical.csv`.")
