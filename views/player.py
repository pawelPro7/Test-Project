import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from utils.data_loader import (
    load_playermatchstats, load_physical, get_teams, get_players, aggregate_player,
    zone_grid_from_marginals, resolve_columns, PHYSICAL_COLUMN_CANDIDATES,
    METRIC_LABELS, POSITION_LABELS_PL, ZONE_ORDER, ZONE_LABELS_PL, LANE_ORDER, LANE_LABELS_PL,
)
from utils.styling import page_header, section_divider, subheader, kpi_card, apply_plotly_theme, COLORS
from utils.viz import (
    zone_heatmap_figure, radar_chart_figure, metric_stats, value_stats,
    player_per90, population_per90, radar_hover_text,
)

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

# Position shown is whichever position the player featured in most often this season,
# not just whatever they happened to play in their most recent match.
most_common_position = (
    player_rows["position"].mode().iloc[0] if "position" in player_rows.columns and not player_rows.empty else None
)
is_gk = most_common_position == "GOALKEEPER"

# match selection: "Team vs Opponent (DD/MM/YYYY)"
match_squads = pms.groupby("matchId")["squadName"].unique().to_dict()


def _opponent(match_id, own_squad):
    others = [s for s in match_squads.get(match_id, []) if s != own_squad]
    return others[0] if others else None


def _match_label(row):
    opp = _opponent(row["matchId"], row["squadName"])
    date_str = pd.to_datetime(row["dateTime"]).strftime("%d/%m/%Y")
    if opp:
        return f"{row['squadName']} vs {opp} ({date_str})"
    return f"{row['squadName']} ({date_str}) — opponent outside dataset"


player_rows["match_label"] = player_rows.apply(_match_label, axis=1)

ALL_MATCHES_LABEL = "All matches average"
match_options = [ALL_MATCHES_LABEL] + player_rows["match_label"].tolist()

# Always default back to "All matches average" whenever this page is freshly opened,
# refreshed, or navigated to from elsewhere - not just on the very first-ever load.
if (st.session_state.get("_navigated_to_new_page")
        or "sel_match" not in st.session_state
        or st.session_state.sel_match not in match_options):
    st.session_state.sel_match = ALL_MATCHES_LABEL

selected_match = st.selectbox("Match", options=match_options, key="sel_match")

if selected_match == ALL_MATCHES_LABEL:
    selected_rows = player_rows
    latest = player_rows.iloc[-1]
else:
    selected_rows = player_rows[player_rows["match_label"] == selected_match]
    latest = selected_rows.iloc[0]

pos_label = POSITION_LABELS_PL.get(most_common_position, most_common_position)
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
  <span class="tag">Last match: {pd.to_datetime(latest['dateTime']).strftime('%d/%m/%Y')}</span>
  </div>
</div>
""", unsafe_allow_html=True)

st.write("")
if selected_match == ALL_MATCHES_LABEL:
    agg = aggregate_player(pms, player_choice)
else:
    agg = aggregate_player(selected_rows, player_choice)

has_minutes = "PLAYDURATION" in pms.columns
minutes_played = agg.get("PLAYDURATION", np.nan) / 60 if has_minutes else np.nan

if not is_gk:
    if has_minutes:
        k0, k1, k2, k3, k4, k5 = st.columns(6)
        with k0:
            st.markdown(kpi_card("Minutes", f"{minutes_played:,.0f}" if pd.notna(minutes_played) else "—"),
                        unsafe_allow_html=True)
        with k1:
            st.markdown(kpi_card("Goals", f"{int(agg.get('GOALS', 0))}"), unsafe_allow_html=True)
        with k2:
            st.markdown(kpi_card("Assists", f"{int(agg.get('ASSISTS', 0))}"), unsafe_allow_html=True)
        with k3:
            st.markdown(kpi_card("Shots", f"{int(agg.get('SHOT_AT_GOAL_NUMBER', 0))}"), unsafe_allow_html=True)
        with k4:
            st.markdown(kpi_card("Shot xG", f"{agg.get('SHOT_XG', 0):.2f}"), unsafe_allow_html=True)
        with k5:
            pa = agg.get("pass_accuracy_pct", np.nan)
            st.markdown(kpi_card("Pass acc", f"{pa:.0f}%" if pd.notna(pa) else "—"), unsafe_allow_html=True)
    else:
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
    gk_rows = player_rows if selected_match == ALL_MATCHES_LABEL else selected_rows
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
    PER90_COLS = {"PACKING_XG", "DRIBBLE_CARRY_SUCCESS", "NUMBER_OF_PRESSES", "OFFENSIVE_TOUCHES"}
    if is_gk:
        radar_cols = {"Successful passes": "SUCCESSFUL_PASSES", "Defensive touches": "DEFENSIVE_TOUCHES",
                      "Claims": "claims", "Catches": "gk_catches",
                      "Saves": "SHOT_AT_GOAL_NUMBER_SAVED", "Defensive PXT": "DEF_PXT_BALL_WIN"}
        compare_pool = pms[pms["position"] == "GOALKEEPER"]
        has_minutes = False  # per-90 conversion only requested for the outfield radar's 4 count metrics
    else:
        compare_pool = pms[pms["position"] != "GOALKEEPER"]
        has_minutes = ("PLAYDURATION" in compare_pool.columns
                        and (compare_pool["PLAYDURATION"].fillna(0) > 0).mean() >= 0.95)
        # pass_accuracy_pct/duel_success_pct are true percentages (successful ÷ total, ×100) and
        # stay per-match regardless; the other four switch to /90 (sum ÷ total minutes × 90) when
        # minutes data is reliably available for the comparison population, else they stay /match
        # rather than showing a fabricated rate.
        count_suffix = " / 90" if has_minutes else " / match"
        radar_cols = {
            "Pass completion %": "pass_accuracy_pct",
            "Duel win %": "duel_success_pct",
            f"Packing xG{count_suffix}": "PACKING_XG",
            f"Successful dribbles{count_suffix}": "DRIBBLE_CARRY_SUCCESS",
            f"Presses{count_suffix}": "NUMBER_OF_PRESSES",
            f"Offensive touches{count_suffix}": "OFFENSIVE_TOUCHES",
        }
    radar_cols = {k: v for k, v in radar_cols.items() if v in pms.columns}
    RADAR_VALUE_FMT = {
        "pass_accuracy_pct": lambda v: f"{v:.1f}%",
        "duel_success_pct": lambda v: f"{v:.1f}%",
        "PACKING_XG": lambda v: f"{v:.2f}",
        "DEF_PXT_BALL_WIN": lambda v: f"{v:.3f}",
    }
    if radar_cols:
        scope_rows = player_rows if selected_match == ALL_MATCHES_LABEL else selected_rows
        player_metric_row = (player_rows[list(radar_cols.values())].mean().to_dict()
                              if selected_match == ALL_MATCHES_LABEL else latest.to_dict())

        stats = []
        for col in radar_cols.values():
            if has_minutes and col in PER90_COLS:
                player_val = player_per90(scope_rows, col)
                population = population_per90(compare_pool, col)
                stats.append(value_stats(population, player_val))
            else:
                stats.append(metric_stats(compare_pool, [col], player_metric_row)[0])

        values = [s["percentile"] if s["percentile"] is not None else 0 for s in stats]
        hover_list = [
            radar_hover_text(stat, RADAR_VALUE_FMT.get(col, lambda v: f"{v:.1f}"))
            for col, stat in zip(radar_cols.values(), stats)
        ]
        fig = radar_chart_figure(list(radar_cols.keys()), {player_choice: values}, height=460,
                                   title="Player profile percentile",
                                   hover_texts={player_choice: hover_list})
        fig.update_layout(
            polar=dict(angularaxis=dict(tickfont=dict(size=12.5))),
            margin=dict(l=50, r=50, t=55, b=35),
        )
        st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})
        pool_desc = "goalkeeper" if is_gk else "outfield-player"
        st.caption(
            f"Percentile (0–100) against all {pool_desc} match performances in the loaded data. "
            "Hover a point for the exact value, percentile, and z-score."
        )
    else:
        st.info("Not enough data to build a profile.")

with col_right:
    section_divider("Activity zones (sum of touches)")
    pitch_cols = [f"OFFENSIVE_TOUCHES_IN_PITCH_POSITION_{z}" for z in ZONE_ORDER]
    lane_cols = [f"OFFENSIVE_TOUCHES_IN_LANE_{l}" for l in LANE_ORDER]
    if all(c in player_rows.columns for c in pitch_cols + lane_cols):
        if selected_match == ALL_MATCHES_LABEL:
            pitch_counts = player_rows[pitch_cols].sum().tolist()
            lane_counts = player_rows[lane_cols].sum().tolist()
        else:
            pitch_counts = latest[pitch_cols].tolist()
            lane_counts = latest[lane_cols].tolist()
        grid = zone_grid_from_marginals(pitch_counts, lane_counts)
        fig = zone_heatmap_figure(grid, [ZONE_LABELS_PL[z] for z in ZONE_ORDER],
                                    [LANE_LABELS_PL[l] for l in LANE_ORDER], height=380,
                                    title="Activity zones — touches")
        st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})
        st.caption("Approximation based on independent marginal distributions (zone × corridor) — see Heatmaps page.")
    else:
        st.info("No zone columns in the data.")

if len(player_rows) > 1:
    section_divider("Form over recent matches")
    metric_label = st.selectbox("Metric", list(METRIC_LABELS.keys()), index=0, key="player_trend_metric")
    metric_col = METRIC_LABELS[metric_label]
    if metric_col in player_rows.columns:
        trend = player_rows[["dateTime", "matchDayIndex", metric_col]].copy()
        trend["match"] = "Matchday " + trend["matchDayIndex"].astype(str)
        fig = px.line(trend, x="dateTime", y=metric_col, markers=True, hover_data=["match"],
                       title=f"{metric_label} by match")
        fig.update_traces(line_color=COLORS["accent"], marker=dict(size=9, color=COLORS["accent"]))
        fig.update_layout(xaxis_title="", yaxis_title=metric_label)
        apply_plotly_theme(fig, height=320, show_legend=False)
        st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})

# ---------------------------------------------------------------- Physicality
PHYS_SPECS = [
    ("totalDistanceM", "Distance / 90"),
    ("hsrDistanceM", "HSR distance / 90"),
    ("numSprints", "Sprints / 90"),
    ("topSpeedKmh", "Peak speed"),
]
GK_MARKERS = {"GK", "GOALKEEPER"}


def _fmt_phys(key, val):
    if val is None:
        return "—"
    if key in ("totalDistanceM", "hsrDistanceM"):
        return f"{val:,.0f} m"
    if key == "numSprints":
        return f"{val:,.1f}"
    if key == "topSpeedKmh":
        return f"{val} km/h"
    return str(val)


def _pct_badge(player_val, league_val):
    if league_val in (None, 0):
        return "", COLORS["text_muted"]
    pct = (player_val - league_val) / league_val * 100
    if abs(pct) < 0.5:
        return "0%", COLORS["text_muted"]
    arrow = "↑" if pct > 0 else "↓"
    color = COLORS["accent_4"] if pct > 0 else COLORS["accent_2"]
    return f"{arrow} {abs(pct):.0f}%", color


def _kpi_card_pct(label, value_str, badge_text, badge_color):
    badge_html = (f'<span class="kpi-pct-badge" style="color:{badge_color};">{badge_text}</span>'
                  if badge_text else "")
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value-row">
            <span class="kpi-value">{value_str}</span>
            {badge_html}
        </div>
    </div>
    """


physical = load_physical()
if not physical.empty:
    colmap = resolve_columns(physical, PHYSICAL_COLUMN_CANDIDATES)
    name_col = colmap.get("playerName")
    if name_col and player_choice in physical[name_col].values:
        section_divider("Physicality (physical.csv)")
        st.caption("Physical output per 90 minutes; based on matches with valid tracking data.")
        p_rows = physical[physical[name_col] == player_choice]

        min_col = colmap.get("minutesPlayed")
        total_minutes = float(p_rows[min_col].sum()) if min_col and min_col in p_rows.columns else 0.0

        def per90(key):
            c = colmap.get(key)
            if not c or c not in p_rows.columns or total_minutes <= 0:
                return None
            return float(p_rows[c].sum()) / total_minutes * 90

        def peak_of(key, decimals=1):
            c = colmap.get(key)
            if not c or c not in p_rows.columns or p_rows[c].dropna().empty:
                return None
            return round(float(p_rows[c].max()), decimals)

        player_values = {
            "totalDistanceM": per90("totalDistanceM"),
            "hsrDistanceM": per90("hsrDistanceM"),
            "numSprints": per90("numSprints"),
            "topSpeedKmh": peak_of("topSpeedKmh"),
        }

        pcol1, _, _, _ = st.columns(4)
        with pcol1:
            compare_key = "compare_physicality"
            currently_on = st.session_state.get(compare_key, False)
            toggle_label = "Hide League Average" if currently_on else "Compare with League Average"
            compare_physical_on = st.toggle(toggle_label, key=compare_key)

        league_values = {k: None for k, _ in PHYS_SPECS}
        if compare_physical_on:
            pos_col = colmap.get("position")
            outfield_phys = (physical[~physical[pos_col].astype(str).str.upper().isin(GK_MARKERS)]
                              if pos_col and pos_col in physical.columns else physical)
            league_min_col = colmap.get("minutesPlayed")
            league_minutes = (float(outfield_phys[league_min_col].sum())
                               if league_min_col and league_min_col in outfield_phys.columns else 0.0)

            def league_per90(key):
                c = colmap.get(key)
                if not c or c not in outfield_phys.columns or league_minutes <= 0:
                    return None
                return float(outfield_phys[c].sum()) / league_minutes * 90

            league_values["totalDistanceM"] = league_per90("totalDistanceM")
            league_values["hsrDistanceM"] = league_per90("hsrDistanceM")
            league_values["numSprints"] = league_per90("numSprints")

            topspeed_col = colmap.get("topSpeedKmh")
            if topspeed_col and topspeed_col in outfield_phys.columns and name_col:
                per_player_peak = outfield_phys.groupby(name_col)[topspeed_col].max()
                league_values["topSpeedKmh"] = (round(float(per_player_peak.mean()), 1)
                                                  if not per_player_peak.empty else None)

        f1, f2, f3, f4 = st.columns(4)
        for col, (key, label) in zip((f1, f2, f3, f4), PHYS_SPECS):
            val = player_values[key]
            val_str = _fmt_phys(key, val)
            with col:
                if compare_physical_on and val is not None and league_values[key] is not None:
                    badge_text, badge_color = _pct_badge(val, league_values[key])
                    st.markdown(_kpi_card_pct(label, val_str, badge_text, badge_color), unsafe_allow_html=True)
                else:
                    st.markdown(kpi_card(label, val_str), unsafe_allow_html=True)

        if compare_physical_on:
            st.write("")
            st.write("")
            subheader("League Average (Outfield Players)")
            g1, g2, g3, g4 = st.columns(4)
            for col, (key, label) in zip((g1, g2, g3, g4), PHYS_SPECS):
                with col:
                    st.markdown(kpi_card(label, _fmt_phys(key, league_values[key])), unsafe_allow_html=True)
    else:
        st.caption("No physical data for this player in `physical.csv`.")
