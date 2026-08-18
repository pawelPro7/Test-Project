import streamlit as st

from utils.data_loader import (
    load_playermatchstats, get_teams, get_players,
    ZONE_ORDER, ZONE_LABELS_PL, LANE_ORDER, LANE_LABELS_PL,
    POSITION_LABELS_PL, zone_grid_from_marginals,
)
from utils.styling import page_header, section_divider, COLORS
from utils.viz import zone_heatmap_figure

pms = load_playermatchstats()
if pms.empty:
    st.error("Missing `data/playermatchstats.csv`.")
    st.stop()

page_header(
    eyebrow="Spatial analysis",
    title="Heatmaps",
    subtitle="Activity zones based on playermatchstats.csv.",
)

ZONE_METRIC_FAMILIES = {
    "Offensive touches": ("OFFENSIVE_TOUCHES_IN_PITCH_POSITION_{z}", "OFFENSIVE_TOUCHES_IN_LANE_{l}", COLORS["accent"]),
    "Bypassed opponents (packing)": ("BYPASSED_OPPONENTS_FROM_PITCH_POSITION_{z}", "BYPASSED_OPPONENTS_FROM_LANE_{l}", COLORS["accent_3"]),
    "Ball recoveries": ("BALL_WIN_NUMBER_FROM_PITCH_POSITION_{z}", "BALL_WIN_NUMBER_IN_LANE_{l}", COLORS["accent_4"]),
}
available_families = {
    label: tpl for label, tpl in ZONE_METRIC_FAMILIES.items()
    if all((tpl[0].format(z=z) in pms.columns) for z in ZONE_ORDER)
    and all((tpl[1].format(l=l) in pms.columns) for l in LANE_ORDER)
}

section_divider("Zone map (playermatchstats.csv)")
c1, c2, c3 = st.columns([1, 1, 1.4])
with c1:
    scope = st.radio("Scope", ["Player", "Team"], horizontal=True, key="hm_scope")
with c2:
    if scope == "Player":
        teams_opt = ["All teams"] + get_teams(pms)
        team_for_players = st.selectbox("Filter by team", teams_opt, key="hm_team_filter")
        target_players = get_players(pms, team_for_players)
        target = st.selectbox("Player", target_players, key="hm_player")
    else:
        target = st.selectbox("Team", get_teams(pms), key="hm_team")
with c3:
    metric_family = st.selectbox("Metric", list(available_families.keys()) or ["No available metrics"], key="hm_metric")

if available_families and metric_family in available_families:
    pitch_tpl, lane_tpl, color = available_families[metric_family]
    subset = pms[pms["playerName"] == target] if scope == "Player" else pms[pms["squadName"] == target]
    pitch_counts = [subset[pitch_tpl.format(z=z)].sum() for z in ZONE_ORDER]
    lane_counts = [subset[lane_tpl.format(l=l)].sum() for l in LANE_ORDER]
    grid = zone_grid_from_marginals(pitch_counts, lane_counts)

    title = f"{metric_family} — {target}"
    if scope == "Player" and not subset.empty and "position" in subset.columns:
        most_common_position = subset["position"].mode().iloc[0]
        position_label = POSITION_LABELS_PL.get(most_common_position, most_common_position)
        title = f"{title} ({position_label})"

    fig = zone_heatmap_figure(grid, [ZONE_LABELS_PL[z] for z in ZONE_ORDER], [LANE_LABELS_PL[l] for l in LANE_ORDER],
                                title=title, height=480, color=color)
    st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})
    st.caption(
        "The grid is the product of two independent marginal distributions (zone × corridor), "
        "because the data report them separately rather than as a joint table — an **approximation**, "
        "not the exact joint distribution of touches on the pitch."
    )
else:
    st.info("The loaded playermatchstats.csv file does not contain a complete set of zone columns for any supported metric.")
