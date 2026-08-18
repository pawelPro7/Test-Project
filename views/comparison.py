import numpy as np
import pandas as pd
import streamlit as st

from utils.data_loader import load_playermatchstats, get_teams, get_players, player_team, POSITION_LABELS_PL
from utils.styling import page_header, section_divider, COLORS
from utils.viz import (
    radar_chart_figure, metric_stats, value_stats,
    player_per90, population_per90, radar_hover_text, ordinal, fmt_zscore,
)

pms = load_playermatchstats()
if pms.empty:
    st.error("Missing `data/playermatchstats.csv`.")
    st.stop()

page_header(
    eyebrow="Comparison",
    title="Player comparison",
    subtitle="Filter by team and position, then compare up to four players on a shared radar chart.",
)

# ---------------------------------------------------------------- position grouping
# Maps this dataset's raw position codes (both the real-data and legacy demo-data spellings)
# onto the five UI groups. GOALKEEPER is deliberately its own group, never merged with outfield.
POSITION_GROUP_MAP = {
    "GOALKEEPER": "Goalkeepers",
    "CENTRAL_DEFENDER": "Centre-backs",
    "LEFT_WINGBACK_DEFENDER": "Full-backs", "RIGHT_WINGBACK_DEFENDER": "Full-backs",
    "FULLBACK_LEFT": "Full-backs", "FULLBACK_RIGHT": "Full-backs",
    "DEFENSE_MIDFIELD": "Midfielders", "DEFENSIVE_MIDFIELD": "Midfielders",
    "CENTRAL_MIDFIELD": "Midfielders", "ATTACKING_MIDFIELD": "Midfielders",
    "LEFT_WINGER": "Forwards", "RIGHT_WINGER": "Forwards",
    "WINGER_LEFT": "Forwards", "WINGER_RIGHT": "Forwards",
    "CENTER_FORWARD": "Forwards",
}
POSITION_OPTIONS = ["All outfield players", "Goalkeepers", "Centre-backs", "Full-backs", "Midfielders", "Forwards"]
MIN_GROUP_SIZE = 15   # below this, fall back to the full outfield population (too small to be meaningful)
MIN_TOTAL_MINUTES = 90  # a player needs at least one full match's worth of minutes to enter a /90 population
MAX_PLAYERS = 4
PLAYER_COLORS = [COLORS["accent"], COLORS["accent_3"], COLORS["accent_2"], COLORS["accent_4"]]

player_group = pms.groupby("playerName")["position"].agg(
    lambda s: POSITION_GROUP_MAP.get(s.mode().iloc[0]) if not s.mode().empty else None
)

# ---------------------------------------------------------------- filters
f1, f2 = st.columns(2)
with f1:
    team_filter = st.selectbox("Team", ["All teams"] + get_teams(pms), key="cmp_team")
with f2:
    if "cmp_position" not in st.session_state or st.session_state.cmp_position not in POSITION_OPTIONS:
        st.session_state.cmp_position = "All outfield players"
    position_filter = st.selectbox("Position", POSITION_OPTIONS, key="cmp_position")

is_goalkeeper_mode = position_filter == "Goalkeepers"


def _position_population(pos_filter):
    """(row-level df, population description, fallback note-or-None) for the given Position filter."""
    if pos_filter == "Goalkeepers":
        players = player_group[player_group == "Goalkeepers"].index
        return pms[pms["playerName"].isin(players)], "goalkeeper", None
    if pos_filter == "All outfield players":
        players = player_group[player_group != "Goalkeepers"].index
        return pms[pms["playerName"].isin(players)], "outfield-player", None
    group_players = player_group[player_group == pos_filter].index
    if len(group_players) >= MIN_GROUP_SIZE:
        return pms[pms["playerName"].isin(group_players)], pos_filter.lower(), None
    fallback_players = player_group[player_group != "Goalkeepers"].index
    note = (f"Only {len(group_players)} {pos_filter.lower()} in the loaded dataset — too few for a reliable "
            "comparison, so percentiles and z-scores below use the full outfield-player population instead.")
    return pms[pms["playerName"].isin(fallback_players)], "outfield-player", note


population_df, population_desc, population_note = _position_population(position_filter)

# ---------------------------------------------------------------- eligible players (team ∩ position, GK/outfield never mixed)
team_eligible = set(get_players(pms, team_filter))
if position_filter == "Goalkeepers":
    position_eligible = set(player_group[player_group == "Goalkeepers"].index)
elif position_filter == "All outfield players":
    position_eligible = set(player_group[player_group != "Goalkeepers"].index)
else:
    position_eligible = set(player_group[player_group == position_filter].index)

eligible_players = sorted(team_eligible & position_eligible)

if len(eligible_players) < 2:
    st.warning("Fewer than 2 players match this Team + Position combination — widen the filters to compare.")
    st.stop()

label_to_name = {}
for n in eligible_players:
    team_n = player_team(pms, n)
    label_to_name[f"{n} — {team_n}" if team_n else n] = n
options = list(label_to_name.keys())

# ---------------------------------------------------------------- player slots (2-4)
if "cmp_num_players" not in st.session_state:
    st.session_state.cmp_num_players = 2
st.session_state.cmp_num_players = min(max(st.session_state.cmp_num_players, 2), MAX_PLAYERS)
num_players = min(st.session_state.cmp_num_players, len(options)) if len(options) >= 2 else 2


def _ensure_valid(key, opts, fallback_idx=0):
    if key not in st.session_state or st.session_state[key] not in opts:
        st.session_state[key] = opts[min(fallback_idx, len(opts) - 1)]


slot_cols = st.columns(num_players)
chosen_labels = []
for i in range(num_players):
    key = f"cmp_player{i + 1}"
    remaining = [o for o in options if o not in chosen_labels] or options
    _ensure_valid(key, remaining, min(i, len(remaining) - 1))
    with slot_cols[i]:
        label = st.selectbox(f"Player {i + 1}", remaining, key=key)
    chosen_labels.append(label)

btn_cols = st.columns([1, 1, 6])
with btn_cols[0]:
    if num_players < MAX_PLAYERS and num_players < len(options):
        if st.button("+ Add player"):
            st.session_state.cmp_num_players = num_players + 1
            st.rerun()
with btn_cols[1]:
    if num_players > 2:
        if st.button("− Remove player"):
            st.session_state.pop(f"cmp_player{num_players}", None)
            st.session_state.cmp_num_players = num_players - 1
            st.rerun()

selected_players = [label_to_name[lbl] for lbl in chosen_labels]

# ---------------------------------------------------------------- radar metric sets
PCT_COLS = {"pass_accuracy_pct", "duel_success_pct", "claims_vs_expected_pct"}
LOWER_IS_BETTER_COLS = set()  # none of the currently-active metrics need reversal; kept for future GK additions
has_minutes = ("PLAYDURATION" in population_df.columns
                and (population_df["PLAYDURATION"].fillna(0) > 0).mean() >= 0.95)
count_suffix = " / 90" if has_minutes else " / match"

OUTFIELD_RADAR_SPECS = {
    f"Progressive carries{count_suffix}": "DRIBBLE_PROGRESSIVE_CARRY",
    "Duel win %": "duel_success_pct",
    "Pass completion %": "pass_accuracy_pct",
    f"Offensive touches{count_suffix}": "OFFENSIVE_TOUCHES",
    f"Presses{count_suffix}": "NUMBER_OF_PRESSES",
    f"Successful dribbles{count_suffix}": "DRIBBLE_CARRY_SUCCESS",
    f"xG{count_suffix}": "SHOT_XG",
    f"Shot-creating actions{count_suffix}": "SHOT_CREATING_ACTIONS",
}
GK_RADAR_SPECS = {
    f"Claims{count_suffix}": "claims",
    f"Catches{count_suffix}": "gk_catches",
    f"Punches{count_suffix}": "gk_punch_parry",
    f"Goals prevented{count_suffix}": "GOALS_PREVENTED",
    "Claim success vs expected %": "claims_vs_expected_pct",
    "Pass completion %": "pass_accuracy_pct",
}

RADAR_SPECS = GK_RADAR_SPECS if is_goalkeeper_mode else OUTFIELD_RADAR_SPECS
RADAR_SPECS = {k: v for k, v in RADAR_SPECS.items() if v in pms.columns}

RADAR_VALUE_FMT = {
    "pass_accuracy_pct": lambda v: f"{v:.1f}%",
    "duel_success_pct": lambda v: f"{v:.1f}%",
    "claims_vs_expected_pct": lambda v: f"{v:.1f}%",
    "SHOT_XG": lambda v: f"{v:.2f}",
    "GOALS_PREVENTED": lambda v: f"{v:.2f}",
    "claims": lambda v: f"{v:.2f}",
    "gk_catches": lambda v: f"{v:.2f}",
    "gk_punch_parry": lambda v: f"{v:.2f}",
}


def _player_stats(player_name):
    """List of {raw, percentile, zscore} dicts, one per RADAR_SPECS column, in RADAR_SPECS order."""
    rows = pms[pms["playerName"] == player_name]
    pct_cols = [c for c in RADAR_SPECS.values() if c in PCT_COLS]
    pct_row = rows[pct_cols].mean().to_dict() if pct_cols else {}
    out = []
    for col in RADAR_SPECS.values():
        higher_is_better = col not in LOWER_IS_BETTER_COLS
        if col in PCT_COLS:
            out.append(metric_stats(population_df, [col], pct_row, higher_is_better=higher_is_better)[0])
        elif has_minutes:
            player_val = player_per90(rows, col)
            population = population_per90(population_df, col, min_total_minutes=MIN_TOTAL_MINUTES)
            out.append(value_stats(population, player_val, higher_is_better=higher_is_better))
        else:
            row_mean = {col: rows[col].mean()}
            out.append(metric_stats(population_df, [col], row_mean, higher_is_better=higher_is_better)[0])
    return out


section_divider("Radar profile (percentile vs comparison population)")
if population_note:
    st.caption(f"ℹ️ {population_note}")
if is_goalkeeper_mode:
    st.caption(f"Goalkeeper-specific metric set ({len(RADAR_SPECS)} axes) — compared only against other goalkeepers.")

player_colors = dict(zip(selected_players, PLAYER_COLORS))
player_labels = dict(zip(selected_players, chosen_labels))
player_stats_cache = {}

if RADAR_SPECS:
    series, hover_texts = {}, {}
    for name in selected_players:
        stats = _player_stats(name)
        player_stats_cache[name] = stats
        label = player_labels[name]
        series[label] = [s["percentile"] if s["percentile"] is not None else 0 for s in stats]
        hover_texts[label] = [
            radar_hover_text(stat, RADAR_VALUE_FMT.get(col, lambda v: f"{v:.1f}"), player_name=label)
            for col, stat in zip(RADAR_SPECS.values(), stats)
        ]

    fig = radar_chart_figure(list(RADAR_SPECS.keys()), series, height=560,
                               title="Player profile percentile", hover_texts=hover_texts)
    fig.update_layout(
        polar=dict(angularaxis=dict(tickfont=dict(size=11.5))),
        margin=dict(l=70, r=70, t=60, b=40),
    )
    st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})
    minutes_note = f" (players need ≥{MIN_TOTAL_MINUTES} total minutes to enter the /90 comparison population)" if has_minutes else ""
    st.caption(
        f"Percentile (0–100) for each metric against the {population_desc} comparison population"
        f"{minutes_note}. Hover a point for that player's exact value, percentile, and z-score."
    )
else:
    st.info("Not enough data to build a radar profile.")
    player_stats_cache = {name: _player_stats(name) for name in selected_players}

# ---------------------------------------------------------------- numeric summary
section_divider("Numeric summary")
if not player_stats_cache:
    player_stats_cache = {name: _player_stats(name) for name in selected_players}


def _fmt_z_summary(z):
    """Same rounding/sign convention as fmt_zscore, except an exact-zero z-score is shown
    without a leading '+' (matches the Numeric Summary's own formatting spec)."""
    return "0.00" if round(z, 2) == 0 else fmt_zscore(z)


def _cell_html(stat, value_fmt):
    if stat["raw"] is None:
        return "<div class='cmp-cell-na'>N/A</div>"
    raw_txt = value_fmt(stat["raw"])
    pct_txt = f"{ordinal(stat['percentile'])} percentile" if stat["percentile"] is not None else "N/A"
    z_txt = f"z = {_fmt_z_summary(stat['zscore'])}" if stat["zscore"] is not None else "N/A"
    return (
        "<div class='cmp-cell'>"
        f"<div class='cmp-cell-raw'>{raw_txt}</div>"
        f"<div class='cmp-cell-pct'>{pct_txt}</div>"
        f"<div class='cmp-cell-z'>{z_txt}</div>"
        "</div>"
    )


def _player_position_label(player_name):
    """The position the player featured in most often (mode), mapped to its display label -
    same convention as the Player page, so it stays correct for both outfield players and GKs."""
    rows = pms[pms["playerName"] == player_name]
    if "position" not in rows.columns or rows.empty:
        return None
    mode = rows["position"].mode()
    if mode.empty:
        return None
    return POSITION_LABELS_PL.get(mode.iloc[0], mode.iloc[0])


def _header_cell_html(name):
    pos = _player_position_label(name)
    pos_line = f"<div class='cmp-header-pos'>Position: {pos}</div>" if pos else ""
    return (
        "<th><div class='cmp-header'>"
        f"<div class='cmp-header-name'><span class='cmp-swatch' style='background:{player_colors[name]}'></span>"
        f"{player_labels[name]}</div>"
        f"{pos_line}"
        "</div></th>"
    )


header_cells = "".join(_header_cell_html(name) for name in selected_players)
body_rows = ""
for i, (metric_label, col) in enumerate(RADAR_SPECS.items()):
    value_fmt = RADAR_VALUE_FMT.get(col, lambda v: f"{v:.1f}")
    cells = "".join(
        f"<td>{_cell_html(player_stats_cache[name][i], value_fmt)}</td>"
        for name in selected_players
    )
    body_rows += f"<tr><td class='cmp-row-label'>{metric_label}</td>{cells}</tr>"

table_html = f"""
<div class="cmp-table-wrap">
<table class="cmp-table">
<thead><tr><th></th>{header_cells}</tr></thead>
<tbody>{body_rows}</tbody>
</table>
</div>
"""
st.markdown(table_html, unsafe_allow_html=True)
