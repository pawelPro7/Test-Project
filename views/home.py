import pandas as pd
import plotly.express as px
import streamlit as st

from utils.data_loader import (
    load_playermatchstats, load_physical, data_status, resolve_columns, PHYSICAL_COLUMN_CANDIDATES,
)
from utils.styling import page_header, section_divider, subheader, kpi_card, apply_plotly_theme, COLORS

pms = load_playermatchstats()
status = data_status()

page_header(
    eyebrow="Championship Season 25/26 · Analytics dashboard",
    title="League Overview",
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

if not status["physical"]["ok"]:
    with st.expander("ℹ️ Note on physical.csv — assumed data schema", expanded=False):
        st.markdown(
            "The structure of this file could not be unambiguously confirmed when building the app, "
            "so the loader assumes a typical schema for this data class (distance, sprints, speed) and "
            "matches columns flexibly (case-insensitive). Replace the file in `data/` with your full export — "
            "if column names differ, update the candidate list in `utils/data_loader.py` (`PHYSICAL_COLUMN_CANDIDATES`)."
        )


def _fmt(value, decimals=1, suffix=""):
    return f"{value:.{decimals}f}{suffix}" if pd.notna(value) else "—"


def _vs_team_heading(prefix, team_name):
    """'{prefix} vs {team_name}' with only team_name colored light blue; rest inherits the caller's color."""
    return f'{prefix} vs <span style="color:{COLORS["accent_3"]};">{team_name}</span>'


def _profile_metrics(df):
    """Attacking / possession / defensive rates for any subset of playermatchstats rows.

    Count-based figures (goals, xG, pressures, ball wins/losses, SCA, progressive passing
    value) are normalized per TEAM-match, not per match: a match has two teams' worth of
    rows, so dividing a league-wide sum by the match count would silently combine both
    sides' totals — inflating the "league average" to roughly double what any single team
    actually produces, and making it not directly comparable to a one-team figure like
    Coventry's own average. Ratio metrics (conversion %, accuracy %) don't have this
    problem since they're already totals-over-totals regardless of how many teams are in df.
    """
    team_matches = df.drop_duplicates(["matchId", "squadName"]).shape[0]
    total_g = int(df["GOALS"].sum()) if "GOALS" in df.columns else 0
    total_s = int(df["SHOT_AT_GOAL_NUMBER"].sum()) if "SHOT_AT_GOAL_NUMBER" in df.columns else 0
    m = {
        "goals_per_match": total_g / max(team_matches, 1),
        "xg_per_match": df["SHOT_XG"].sum() / max(team_matches, 1) if "SHOT_XG" in df.columns else float("nan"),
        "shot_conversion": (total_g / total_s * 100) if total_s > 0 else float("nan"),
        "shots_on_target": float("nan"),
        "pass_accuracy": float("nan"),
        "passing_under_pressure": float("nan"),
    }
    if {"SHOT_AT_GOAL_NUMBER_ON_TARGET", "SHOT_AT_GOAL_NUMBER"}.issubset(df.columns) and total_s > 0:
        m["shots_on_target"] = df["SHOT_AT_GOAL_NUMBER_ON_TARGET"].sum() / total_s * 100
    if {"SUCCESSFUL_PASSES", "UNSUCCESSFUL_PASSES"}.issubset(df.columns):
        s, u = df["SUCCESSFUL_PASSES"].sum(), df["UNSUCCESSFUL_PASSES"].sum()
        m["pass_accuracy"] = s / (s + u) * 100 if (s + u) > 0 else float("nan")
    if {"SUCCESSFUL_PASSES_UNDER_PRESSURE", "PASSES_UNDER_PRESSURE"}.issubset(df.columns):
        sp, tp = df["SUCCESSFUL_PASSES_UNDER_PRESSURE"].sum(), df["PASSES_UNDER_PRESSURE"].sum()
        m["passing_under_pressure"] = sp / tp * 100 if tp > 0 else float("nan")
    m["prog_passing_value90"] = (df["PXT_PASS_PRO"].sum() / team_matches
                                   if "PXT_PASS_PRO" in df.columns and team_matches > 0 else float("nan"))
    m["sca90"] = (df["SHOT_CREATING_ACTIONS"].sum() / team_matches
                   if "SHOT_CREATING_ACTIONS" in df.columns and team_matches > 0 else float("nan"))
    m["pressures90"] = (df["NUMBER_OF_PRESSURES_EVENT"].sum() / team_matches
                          if "NUMBER_OF_PRESSURES_EVENT" in df.columns and team_matches > 0 else float("nan"))
    m["recoveries90"] = (df["BALL_WIN_NUMBER"].sum() / team_matches
                           if "BALL_WIN_NUMBER" in df.columns and team_matches > 0 else float("nan"))
    m["ball_losses90"] = (df["BALL_LOSS_NUMBER"].sum() / team_matches
                            if "BALL_LOSS_NUMBER" in df.columns and team_matches > 0 else float("nan"))
    return m


def _high_intensity_per90(physical_df, colmap, team_name=None):
    """League-wide, or single-team (substring match on squad name), high-intensity actions per team-match.

    Uses physical.csv's own match_id + team-name columns to count team-matches directly
    (same per-team-match normalization as _profile_metrics), rather than dividing by total
    player-minutes, which would average across however many players physical.csv happens
    to track per match rather than giving a whole-team total.
    """
    if physical_df.empty:
        return float("nan")
    hi_col = colmap.get("highIntensityActions")
    squad_col = colmap.get("squadName")
    match_col = colmap.get("matchId")
    if not hi_col or not squad_col or not match_col:
        return float("nan")
    sub = physical_df
    if team_name is not None:
        sub = physical_df[physical_df[squad_col].astype(str).str.contains(team_name, case=False, na=False)]
        if sub.empty:
            return float("nan")
    team_matches = sub.drop_duplicates([match_col, squad_col]).shape[0]
    return sub[hi_col].sum() / team_matches if team_matches > 0 else float("nan")


def _compare_sign(league_val, team_val, higher_is_better):
    """(sign, color) pointing toward whichever side is the better performer — league (left) or
    Coventry (right) — not literal numeric magnitude. '<' + green means Coventry is better;
    '>' + red means the league average is better. For a lower-is-better metric (e.g. ball
    losses), Coventry having the smaller number still renders as '<' + green, even though that's
    not a true numeric inequality read left-to-right.
    """
    if pd.isna(league_val) or pd.isna(team_val):
        return "—", COLORS["text_muted"]
    if abs(team_val - league_val) < 1e-9:
        return "=", COLORS["text_muted"]
    team_higher = team_val > league_val
    team_better = team_higher if higher_is_better else not team_higher
    return ("<", COLORS["accent_4"]) if team_better else (">", COLORS["accent_2"])


def _compare_card(label, league_str, team_str, sign, sign_color):
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-compare-row">
            <span class="kpi-compare-league">{league_str}</span>
            <span class="kpi-compare-sign" style="color:{sign_color};">{sign}</span>
            <span class="kpi-compare-team">{team_str}</span>
        </div>
    </div>
    """


def _render_group(subheader_label, specs, metrics):
    subheader(subheader_label)
    cols = st.columns(4)
    for col, (key, label, dec, suffix, _) in zip(cols, specs):
        with col:
            st.markdown(kpi_card(label, _fmt(metrics.get(key, float("nan")), dec, suffix)), unsafe_allow_html=True)


def _render_compare_group(subheader_label, specs, league_metrics, team_metrics):
    subheader(_vs_team_heading(subheader_label, COMPARE_TEAM), color=COLORS["text"])
    cols = st.columns(4)
    for col, (key, label, dec, suffix, higher_is_better) in zip(cols, specs):
        league_val = league_metrics.get(key, float("nan"))
        team_val = team_metrics.get(key, float("nan"))
        sign, sign_color = _compare_sign(league_val, team_val, higher_is_better)
        with col:
            st.markdown(
                _compare_card(label, _fmt(league_val, dec, suffix), _fmt(team_val, dec, suffix), sign, sign_color),
                unsafe_allow_html=True,
            )


ATTACKING_SPECS = [
    ("goals_per_match", "Goals / match", 2, "", True),
    ("xg_per_match", "xG / match", 2, "", True),
    ("shot_conversion", "Shot conversion", 1, "%", True),
    ("shots_on_target", "Shots on target", 1, "%", True),
]
POSSESSION_SPECS = [
    ("pass_accuracy", "Pass accuracy", 1, "%", True),
    ("passing_under_pressure", "Passing under pressure", 1, "%", True),
    ("prog_passing_value90", "Progressive passing value / 90", 3, "", True),
    ("sca90", "Shot-creating actions / 90", 1, "", True),
]
DEFENSIVE_SPECS = [
    ("pressures90", "Pressures / 90", 1, "", True),
    ("recoveries90", "Ball recoveries / 90", 1, "", True),
    ("ball_losses90", "Ball losses / 90", 1, "", False),
    ("hi_per90", "High-intensity actions / 90", 1, "", True),
]


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
    st.markdown(kpi_card("Goals", f"{total_goals}", f"{goals_per_match:.2f} combined goals / match"),
                unsafe_allow_html=True)
with k5:
    st.markdown(
        kpi_card("Shot conversion", _fmt(shot_conversion, 1, "%"),
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
                      title="Top Scorers", text="GOALS")
        fig.update_traces(marker_color=COLORS["accent"], textposition="outside", cliponaxis=False)
        fig.update_layout(yaxis_title="", xaxis_title="")
        fig.update_xaxes(range=[0, top_scorers["GOALS"].max() * 1.2])
        apply_plotly_theme(fig, height=320, show_legend=False)
        st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})
    else:
        st.info("No goals recorded in the data.")

with lead_col2:
    top_assists = (pms.groupby("playerName", as_index=False)["ASSISTS"].sum()
                   .query("ASSISTS > 0").sort_values("ASSISTS", ascending=False).head(8))
    if not top_assists.empty:
        fig = px.bar(top_assists.sort_values("ASSISTS"), x="ASSISTS", y="playerName", orientation="h",
                      title="Most Assists", text="ASSISTS")
        fig.update_traces(marker_color=COLORS["accent_3"], textposition="outside", cliponaxis=False)
        fig.update_layout(yaxis_title="", xaxis_title="")
        fig.update_xaxes(range=[0, top_assists["ASSISTS"].max() * 1.2])
        apply_plotly_theme(fig, height=320, show_legend=False)
        st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})
    else:
        st.info("No assists recorded in the data.")

with lead_col3:
    top_shot_xg = (pms.groupby("playerName", as_index=False)["SHOT_XG"].sum()
                   .sort_values("SHOT_XG", ascending=False).head(8))
    if not top_shot_xg.empty and top_shot_xg["SHOT_XG"].sum() > 0:
        fig = px.bar(top_shot_xg.sort_values("SHOT_XG"), x="SHOT_XG", y="playerName", orientation="h",
                      title="Shot xG (total)", text=top_shot_xg.sort_values("SHOT_XG")["SHOT_XG"].round(2))
        fig.update_traces(marker_color=COLORS["accent_4"], textposition="outside", cliponaxis=False)
        fig.update_layout(yaxis_title="", xaxis_title="")
        fig.update_xaxes(range=[0, top_shot_xg["SHOT_XG"].max() * 1.2])
        apply_plotly_theme(fig, height=320, show_legend=False)
        st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})
    else:
        st.info("No Shot xG data.")

# ---------------------------------------------------------------- League profile
section_divider("League profile")

COMPARE_TEAM = "Coventry City"

league_metrics = _profile_metrics(pms)
physical = load_physical()
phys_colmap = resolve_columns(physical, PHYSICAL_COLUMN_CANDIDATES) if not physical.empty else {}
league_metrics["hi_per90"] = _high_intensity_per90(physical, phys_colmap)

_render_group("Attacking (league average)", ATTACKING_SPECS, league_metrics)
_render_group("Possession & passing (league average)", POSSESSION_SPECS, league_metrics)
_render_group("Defensive & physical (league average)", DEFENSIVE_SPECS, league_metrics)

tcol1, _, _, _ = st.columns(4)
with tcol1:
    compare_on = st.toggle(f"Compare vs {COMPARE_TEAM}", key="compare_coventry")

if compare_on:
    team_df = pms[pms["squadName"] == COMPARE_TEAM]
    if team_df.empty:
        st.warning(f"No `{COMPARE_TEAM}` rows found in `playermatchstats.csv`.")
    else:
        st.write("")
        section_divider(_vs_team_heading("League Profile", COMPARE_TEAM), color=COLORS["text"])
        team_metrics = _profile_metrics(team_df)
        team_metrics["hi_per90"] = _high_intensity_per90(physical, phys_colmap, team_name=COMPARE_TEAM)

        _render_compare_group("Attacking (league average)", ATTACKING_SPECS, league_metrics, team_metrics)
        _render_compare_group("Possession & passing (league average)", POSSESSION_SPECS, league_metrics, team_metrics)
        _render_compare_group("Defensive & physical (league average)", DEFENSIVE_SPECS, league_metrics, team_metrics)
