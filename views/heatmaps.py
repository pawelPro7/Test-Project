import numpy as np
import pandas as pd
import streamlit as st

from utils.data_loader import (
    load_playermatchstats, load_events, get_teams, get_players, resolve_columns,
    EVENTS_COLUMN_CANDIDATES, ZONE_ORDER, ZONE_LABELS_PL, LANE_ORDER, LANE_LABELS_PL,
    zone_grid_from_marginals,
)
from utils.styling import page_header, section_divider, COLORS
from utils.viz import zone_heatmap_figure, event_heatmap_figure, shot_map_figure, normalize_xy

pms = load_playermatchstats()
if pms.empty:
    st.error("Brak `data/playermatchstats.csv`.")
    st.stop()

page_header(
    eyebrow="Spatial analysis",
    title="Heatmaps",
    subtitle="Activity zones based on playermatchstats.csv and — if available — real event maps from events.csv.",
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
    fig = zone_heatmap_figure(grid, [ZONE_LABELS_PL[z] for z in ZONE_ORDER], [LANE_LABELS_PL[l] for l in LANE_ORDER],
                                title=f"{metric_family} — {target}", height=480, color=color)
    st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})
    st.caption(
        "The grid is the product of two independent marginal distributions (zone × corridor), "
        "because the data report them separately rather than as a joint table — an **approximation**, "
        "not the exact joint distribution of touches on the pitch."
    )
else:
    st.info("The loaded playermatchstats.csv file does not contain a complete set of zone columns for any supported metric.")

# ---------------------------------------------------------------- Zdarzenia (prawdziwe x/y)
events = load_events()
section_divider("Event map (events.csv)")

if events.empty:
    st.info("No `data/events.csv` file — this section will appear automatically when the file is available in the data/ folder.")
else:
    colmap = resolve_columns(events, EVENTS_COLUMN_CANDIDATES)
    x_col, y_col = colmap.get("x"), colmap.get("y")
    if not x_col or not y_col:
        st.warning(
            "Nie udało się rozpoznać kolumn współrzędnych (x/y) w events.csv. "
            "Zmapuj je ręcznie w `utils/data_loader.py` → `EVENTS_COLUMN_CANDIDATES`, jeśli Twój plik używa innych nazw."
        )
    else:
        e1, e2, e3 = st.columns([1, 1, 1.4])
        with e1:
            ev_scope = st.radio("Scope", ["Player", "Team", "All"], horizontal=True, key="ev_scope")
        name_col, squad_col = colmap.get("playerName"), colmap.get("squadName")
        ev_target = None
        with e2:
            if ev_scope == "Player" and name_col:
                ev_target = st.selectbox("Player", sorted(events[name_col].dropna().unique()), key="ev_player")
            elif ev_scope == "Team" and squad_col:
                ev_target = st.selectbox("Team", sorted(events[squad_col].dropna().unique()), key="ev_team")
        type_col = colmap.get("eventType")
        with e3:
            if type_col:
                types = sorted(events[type_col].dropna().unique())
                chosen_types = st.multiselect("Event types", types, default=types, key="ev_types")
            else:
                chosen_types = None

        sub = events.copy()
        if ev_scope == "Zawodnik" and name_col and ev_target:
            sub = sub[sub[name_col] == ev_target]
        elif ev_scope == "Drużyna" and squad_col and ev_target:
            sub = sub[sub[squad_col] == ev_target]
        if type_col and chosen_types is not None:
            sub = sub[sub[type_col].isin(chosen_types)]

        if sub.empty:
            st.info("Brak zdarzeń dla wybranych filtrów.")
        else:
            xmax = pd.to_numeric(events[x_col], errors="coerce").max()
            x_norm = normalize_xy(pd.to_numeric(sub[x_col], errors="coerce"), xmax)
            y_norm = normalize_xy(pd.to_numeric(sub[y_col], errors="coerce"), xmax)
            label = ev_target if ev_target else "all events"
            fig = event_heatmap_figure(x_norm, y_norm, title=f"Event map — {label}", height=480)
            st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})
            st.caption(f"Map built from {len(sub)} events with real coordinates (columns `{x_col}` / `{y_col}`).")

            shot_mask = sub[type_col].astype(str).str.contains("shot", case=False, na=False) if type_col else pd.Series(False, index=sub.index)
            if shot_mask.any():
                section_divider("Shot map")
                shots = sub[shot_mask].copy()
                xg_col, outcome_col = colmap.get("xG"), colmap.get("outcome")
                xg_vals = pd.to_numeric(shots[xg_col], errors="coerce") if xg_col else pd.Series(np.nan, index=shots.index)
                outcome_flag = shots[outcome_col].astype(str).str.upper().str.contains("SUCCESS") if outcome_col else pd.Series(False, index=shots.index)
                sx = normalize_xy(pd.to_numeric(shots[x_col], errors="coerce"), xmax)
                sy = normalize_xy(pd.to_numeric(shots[y_col], errors="coerce"), xmax)
                fig2 = shot_map_figure(sx, sy, xg_vals, outcome_flag, height=460, title=f"Shots — {label}")
                st.plotly_chart(fig2, width='stretch', config={"displayModeBar": False})
                st.caption(
                    "Marker size ∝ shot xG. Color indicates action outcome according to the outcome column (shown as “success” vs others), not confirmed goals."
                )
