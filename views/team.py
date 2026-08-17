import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from utils.data_loader import (
    load_playermatchstats, load_physical, get_teams, resolve_columns, match_team_name,
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
                                  index=list(METRIC_LABELS.keys()).index("Goals"), key="team_rank_metric")
    metric_col = METRIC_LABELS[metric_label]
    if metric_col in team_df.columns:
        ranking = (team_df.groupby("playerName", as_index=False)[metric_col].sum()
                   .sort_values(metric_col, ascending=False).head(20))
        fig = px.bar(ranking.sort_values(metric_col), x=metric_col, y="playerName", orientation="h",
                      text=ranking.sort_values(metric_col)[metric_col].round(2),
                      title=f"{metric_label} — {team_choice}")
        fig.update_traces(marker_color=COLORS["accent"], textposition="outside", cliponaxis=False,
                           textfont_size=15)
        fig.update_layout(yaxis_title="", xaxis_title=metric_label, bargap=0.3)
        fig.update_yaxes(tickfont=dict(size=14.5), automargin=True)
        apply_plotly_theme(fig, height=520, show_legend=False)
        fig.update_layout(margin=dict(l=4, r=10, t=50, b=10),
                            title=dict(x=0.01, xanchor="left"))
        st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})

with right:
    section_divider("Team dominance zones")
    pitch_cols = [f"OFFENSIVE_TOUCHES_IN_PITCH_POSITION_{z}" for z in ZONE_ORDER]
    lane_cols = [f"OFFENSIVE_TOUCHES_IN_LANE_{l}" for l in LANE_ORDER]
    if all(c in team_df.columns for c in pitch_cols + lane_cols):
        grid = zone_grid_from_marginals(team_df[pitch_cols].sum().tolist(), team_df[lane_cols].sum().tolist())
        fig = zone_heatmap_figure(grid, [ZONE_LABELS_PL[z] for z in ZONE_ORDER],
                                    [LANE_LABELS_PL[l] for l in LANE_ORDER], height=420, color=COLORS["accent_3"],
                                    title=f"Touches by zone — {team_choice}")
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
section_divider("Team physicals (physical.csv)")
if not physical.empty:
    colmap = resolve_columns(physical, PHYSICAL_COLUMN_CANDIDATES)
    squad_col = colmap.get("squadName")
    dist_col, hsr_col, name_col = colmap.get("totalDistanceM"), colmap.get("hsrDistanceM"), colmap.get("playerName")

    matched_phys_team = None
    if squad_col:
        phys_team_names = physical[squad_col].dropna().unique().tolist()
        matched_phys_team = match_team_name(team_choice, phys_team_names)

    if matched_phys_team and dist_col and name_col:
        t_phys = physical[physical[squad_col] == matched_phys_team]
        agg_phys = t_phys.groupby(name_col, as_index=False)[[c for c in [dist_col, hsr_col] if c]].mean()
        agg_phys["dist_km"] = agg_phys[dist_col] / 1000
        agg_phys = agg_phys.sort_values("dist_km")
        n_rows = len(agg_phys)
        fig = px.bar(agg_phys, x="dist_km", y=name_col, orientation="h",
                      text=[f"{v:.1f} km" for v in agg_phys["dist_km"]],
                      title="Average distance per match (km)")
        fig.update_traces(marker_color=COLORS["accent_4"], textposition="outside", cliponaxis=False,
                           textfont_size=14)
        fig.update_layout(yaxis_title="", xaxis_title="km", bargap=0.25)
        fig.update_yaxes(tickfont=dict(size=14), automargin=True)
        fig.update_xaxes(dtick=2)
        apply_plotly_theme(fig, height=max(400, 29 * n_rows + 100), show_legend=False)
        fig.update_layout(margin=dict(l=4, r=10, t=50, b=10),
                            title=dict(x=0.01, xanchor="left", font=dict(size=15.5)))
        st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})
    else:
        st.caption(f"No physical-tracking data available for {team_choice}.")
else:
    st.info("`physical.csv` not found.")
