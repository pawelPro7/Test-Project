import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from utils.data_loader import (
    load_playermatchstats, load_physical, get_teams, resolve_columns,
    PHYSICAL_COLUMN_CANDIDATES, METRIC_LABELS, POSITION_LABELS_PL,
    ZONE_ORDER, ZONE_LABELS_PL, LANE_ORDER, LANE_LABELS_PL, zone_grid_from_marginals,
)
from utils.styling import page_header, section_divider, kpi_card, apply_plotly_theme, COLORS
from utils.viz import zone_heatmap_figure

pms = load_playermatchstats()
if pms.empty:
    st.error("Missing `data/playermatchstats.csv`.")
    st.stop()

page_header(
    eyebrow="Directory",
    title="Team",
    subtitle="Select a team to view aggregated stats, leaders and zones of dominance on the pitch.",
)

teams = get_teams(pms)
if "sel_team_page" not in st.session_state or st.session_state.sel_team_page not in teams:
    st.session_state.sel_team_page = st.session_state.get("sel_team") if st.session_state.get("sel_team") in teams else teams[0]
team_choice = st.selectbox("Team", teams, key="sel_team_page")

team_df = pms[pms["squadName"] == team_choice]
n_matches = team_df["matchId"].nunique()
n_players = team_df["playerId"].nunique()
goals = int(team_df["GOALS"].sum())
xg = team_df["SHOT_XG"].sum()
packing = team_df["PACKING_XG"].sum()
pass_acc = team_df["pass_accuracy_pct"].mean() if "pass_accuracy_pct" in team_df.columns else np.nan

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.markdown(kpi_card("Matches", f"{n_matches}"), unsafe_allow_html=True)
with k2:
    st.markdown(kpi_card("Players in squad", f"{n_players}"), unsafe_allow_html=True)
with k3:
    st.markdown(kpi_card("Goals", f"{goals}", f"{xg:.2f} xG total"), unsafe_allow_html=True)
with k4:
    st.markdown(kpi_card("Packing xG", f"{packing:.2f}"), unsafe_allow_html=True)
with k5:
    st.markdown(kpi_card("Avg. pass acc", f"{pass_acc:.0f}%" if pd.notna(pass_acc) else "—"), unsafe_allow_html=True)

st.write("")
left, right = st.columns([3, 2])

with left:
    section_divider("Player rankings")
    metric_label = st.selectbox("Ranking metric", list(METRIC_LABELS.keys()),
                                  index=list(METRIC_LABELS.keys()).index("Gole"), key="team_rank_metric")
    metric_col = METRIC_LABELS[metric_label]
    if metric_col in team_df.columns:
        ranking = (team_df.groupby("playerName", as_index=False)[metric_col].sum()
                   .sort_values(metric_col, ascending=False).head(20))
        fig = px.bar(ranking.sort_values(metric_col), x=metric_col, y="playerName", orientation="h",
                      text=ranking.sort_values(metric_col)[metric_col].round(2))
        fig.update_traces(marker_color=COLORS["accent"], textposition="outside", cliponaxis=False)
        fig.update_layout(yaxis_title="", xaxis_title=metric_label)
        apply_plotly_theme(fig, height=420, show_legend=False)
        st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})

with right:
    section_divider("Team dominance zones")
    pitch_cols = [f"OFFENSIVE_TOUCHES_IN_PITCH_POSITION_{z}" for z in ZONE_ORDER]
    lane_cols = [f"OFFENSIVE_TOUCHES_IN_LANE_{l}" for l in LANE_ORDER]
    if all(c in team_df.columns for c in pitch_cols + lane_cols):
        grid = zone_grid_from_marginals(team_df[pitch_cols].sum().tolist(), team_df[lane_cols].sum().tolist())
        fig = zone_heatmap_figure(grid, [ZONE_LABELS_PL[z] for z in ZONE_ORDER],
                                    [LANE_LABELS_PL[l] for l in LANE_ORDER], height=420, color=COLORS["accent_3"])
        st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})
    else:
        st.info("No zone columns in the data.")

section_divider("Full squad — stats in data")
show_cols = ["playerName", "position_pl", "age", "GOALS", "ASSISTS", "SHOT_XG", "PACKING_XG",
             "SUCCESSFUL_PASSES", "UNSUCCESSFUL_PASSES", "pass_accuracy_pct",
             "WON_GROUND_DUELS", "WON_AERIAL_DUELS", "BALL_WIN_NUMBER", "BALL_LOSS_NUMBER"]
show_cols = [c for c in show_cols if c in team_df.columns]
roster = (team_df.groupby(["playerName"], as_index=False)
          .agg({c: ("first" if c in ("position_pl", "age") else "sum") for c in show_cols if c != "playerName"}))
if "pass_accuracy_pct" in roster.columns:
    roster["pass_accuracy_pct"] = roster["pass_accuracy_pct"].round(1)
roster = roster.rename(columns={
    "playerName": "Player", "position_pl": "Position", "age": "Age", "GOALS": "Goals", "ASSISTS": "Assists",
    "SHOT_XG": "Shot xG", "PACKING_XG": "Packing xG", "SUCCESSFUL_PASSES": "Successful passes",
    "UNSUCCESSFUL_PASSES": "Unsuccessful passes", "pass_accuracy_pct": "Pass acc %",
    "WON_GROUND_DUELS": "Ground duels (W)", "WON_AERIAL_DUELS": "Aerial duels (W)",
    "BALL_WIN_NUMBER": "Ball wins", "BALL_LOSS_NUMBER": "Ball losses",
})
st.dataframe(roster.sort_values("Goals", ascending=False), width='stretch', hide_index=True)

physical = load_physical()
if not physical.empty:
    colmap = resolve_columns(physical, PHYSICAL_COLUMN_CANDIDATES)
    squad_col = colmap.get("squadName")
    if squad_col and team_choice in physical[squad_col].values:
        section_divider("Team physicals (physical.csv)")
        t_phys = physical[physical[squad_col] == team_choice]
        dist_col, hsr_col, name_col = colmap.get("totalDistanceM"), colmap.get("hsrDistanceM"), colmap.get("playerName")
        if dist_col and name_col:
            agg_phys = t_phys.groupby(name_col, as_index=False)[[c for c in [dist_col, hsr_col] if c]].mean()
            fig = px.bar(agg_phys.sort_values(dist_col), x=dist_col, y=name_col, orientation="h",
                          title="Average distance per match (m)")
            fig.update_traces(marker_color=COLORS["accent_4"])
            fig.update_layout(yaxis_title="", xaxis_title="meters")
            apply_plotly_theme(fig, height=380, show_legend=False)
            st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})
