"""
Data loading and preparation for the app.

playermatchstats.csv has a confirmed, exact schema (verified against the sample
provided by the user), so we reference its columns directly.

physical.csv and events.csv did NOT have a confirmed schema when this app was
built (the user uploaded the same file three times), so every access to their
columns goes through find_column() - a flexible, case-insensitive column
"matcher". If you replace these files with real exports that use different
column names, just extend the candidate lists below (see
PHYSICAL_COLUMN_CANDIDATES / EVENTS_COLUMN_CANDIDATES).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

ZONE_ORDER = ["OWN_BOX", "FIRST_THIRD", "MIDDLE_THIRD", "FINAL_THIRD", "OPPONENT_BOX"]
ZONE_LABELS_PL = {
    "OWN_BOX": "Own penalty box", "FIRST_THIRD": "First third",
    "MIDDLE_THIRD": "Middle third", "FINAL_THIRD": "Final third",
    "OPPONENT_BOX": "Opponent penalty box",
}
LANE_ORDER = ["RIGHT_WING", "RIGHT_HALF_SPACE", "CENTER", "LEFT_HALF_SPACE", "LEFT_WING"]
LANE_LABELS_PL = {
    "RIGHT_WING": "Right wing", "RIGHT_HALF_SPACE": "Right half-space",
    "CENTER": "Center", "LEFT_HALF_SPACE": "Left half-space", "LEFT_WING": "Left wing",
}

POSITION_LABELS_PL = {
    "GOALKEEPER": "Goalkeeper", "CENTRAL_DEFENDER": "Central defender",
    "FULLBACK_RIGHT": "Right-back", "FULLBACK_LEFT": "Left-back",
    "DEFENSIVE_MIDFIELD": "Defensive midfielder", "CENTRAL_MIDFIELD": "Central midfielder",
    "ATTACKING_MIDFIELD": "Attacking midfielder", "WINGER_RIGHT": "Right winger",
    "WINGER_LEFT": "Left winger", "CENTER_FORWARD": "Center forward",
}

# Key metrics used in the UI: display label -> data column name.
METRIC_LABELS = {
    "Goals": "GOALS",
    "Assists": "ASSISTS",
    "xG (Shot xG)": "SHOT_XG",
    "Packing xG": "PACKING_XG",
    "Successful passes": "SUCCESSFUL_PASSES",
    "Unsuccessful passes": "UNSUCCESSFUL_PASSES",
    "Offensive touches": "OFFENSIVE_TOUCHES",
    "Defensive touches": "DEFENSIVE_TOUCHES",
    "Ground duels won": "WON_GROUND_DUELS",
    "Ground duels lost": "LOST_GROUND_DUELS",
    "Aerial duels won": "WON_AERIAL_DUELS",
    "Aerial duels lost": "LOST_AERIAL_DUELS",
    "Shots": "SHOT_AT_GOAL_NUMBER",
    "Ball wins": "BALL_WIN_NUMBER",
    "Ball losses": "BALL_LOSS_NUMBER",
    "Bypassed opponents (packing)": "BYPASSED_OPPONENTS",
    "Bypassed defenders (packing)": "BYPASSED_DEFENDERS",
    "PXT - passes": "PXT_PASS",
    "PXT - dribble": "PXT_DRIBBLE",
    "PXT - ball win": "PXT_BALL_WIN",
    "Fouls": "NUMBER_OF_FOULS",
    "Fouls won": "NUMBER_OF_FOULS_WON",
    "Shot creating actions (SCA)": "SHOT_CREATING_ACTIONS",
    "Dribble (successful carry)": "DRIBBLE_CARRY",
}

PHYSICAL_COLUMN_CANDIDATES = {
    "matchId": ["matchId", "match_id"],
    "playerId": ["playerId", "player_id"],
    "playerName": ["playerName", "player_name", "name"],
    "squadId": ["squadId", "squad_id", "teamId", "team_id"],
    "squadName": ["squadName", "squad_name", "teamName", "team_name"],
    "position": ["position"],
    "minutesPlayed": ["minutesPlayed", "minutes_played", "minutes", "minutes_full_all"],
    "totalDistanceM": ["totalDistanceM", "total_distance", "distance", "totalDistance", "total_distance_full_all"],
    "distancePer90M": ["distancePer90M", "distance_per_90"],
    "hsrDistanceM": ["hsrDistanceM", "hsr_distance", "highSpeedRunningDistance", "hsr_distance_full_all"],
    "sprintDistanceM": ["sprintDistanceM", "sprint_distance", "sprint_distance_full_all"],
    "numSprints": ["numSprints", "num_sprints", "sprints", "sprint_count_full_all"],
    "topSpeedKmh": ["topSpeedKmh", "top_speed", "maxSpeed", "peak_velocity"],
    "accelerations": ["accelerations", "num_accelerations"],
    "decelerations": ["decelerations", "num_decelerations"],
    "highIntensityActions": ["highIntensityActions", "high_intensity_actions", "hi_count_full_all"],
}

EVENTS_COLUMN_CANDIDATES = {
    "matchId": ["matchId", "match_id"],
    "playerId": ["playerId", "player_id"],
    "playerName": ["playerName", "player_name", "name"],
    "squadId": ["squadId", "squad_id", "teamId", "team_id"],
    "squadName": ["squadName", "squad_name", "teamName", "team_name"],
    "eventType": ["eventType", "event_type", "type"],
    "outcome": ["outcome", "result", "success"],
    "x": ["x", "X", "startX", "start_x", "posX", "locationX", "location_x"],
    "y": ["y", "Y", "startY", "start_y", "posY", "locationY", "location_y"],
    "endX": ["endX", "end_x", "toX"],
    "endY": ["endY", "end_y", "toY"],
    "minute": ["minute", "min"],
    "xG": ["xG", "xg", "shotXg", "SHOT_XG"],
}


def find_column(df: pd.DataFrame, candidates) -> str | None:
    """Case-insensitive match of the first candidate column found in the list."""
    if df is None or df.empty:
        return None
    lower_map = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in lower_map:
            return lower_map[cand.lower()]
    return None


def resolve_columns(df: pd.DataFrame, candidates_map: dict) -> dict:
    """Returns {logical_key: column_name_in_df or None} for the whole candidates map."""
    return {key: find_column(df, cands) for key, cands in candidates_map.items()}


@st.cache_data(show_spinner=False)
def load_playermatchstats() -> pd.DataFrame:
    path = DATA_DIR / "playermatchstats.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    if "dateTime" in df.columns:
        df["dateTime"] = pd.to_datetime(df["dateTime"], errors="coerce", utc=True)
    if "birthdate" in df.columns:
        df["_birthdate_parsed"] = pd.to_datetime(df["birthdate"], errors="coerce")
        ref = df["dateTime"].max() if "dateTime" in df.columns and df["dateTime"].notna().any() else pd.Timestamp.utcnow()
        ref = ref.tz_localize(None) if hasattr(ref, "tzinfo") and ref.tzinfo is not None else ref
        df["age"] = ((ref - df["_birthdate_parsed"]).dt.days / 365.25).round().astype("Int64")
    if "position" in df.columns:
        df["position_pl"] = df["position"].map(POSITION_LABELS_PL).fillna(df["position"])
    if {"SUCCESSFUL_PASSES", "UNSUCCESSFUL_PASSES"}.issubset(df.columns):
        total_passes = df["SUCCESSFUL_PASSES"] + df["UNSUCCESSFUL_PASSES"]
        df["pass_accuracy_pct"] = np.where(total_passes > 0, df["SUCCESSFUL_PASSES"] / total_passes * 100, np.nan)
    if {"WON_AERIAL_DUELS", "LOST_AERIAL_DUELS"}.issubset(df.columns):
        total_aer = df["WON_AERIAL_DUELS"] + df["LOST_AERIAL_DUELS"]
        df["aerial_win_pct"] = np.where(total_aer > 0, df["WON_AERIAL_DUELS"] / total_aer * 100, np.nan)
    if {"WON_GROUND_DUELS", "LOST_GROUND_DUELS"}.issubset(df.columns):
        total_gd = df["WON_GROUND_DUELS"] + df["LOST_GROUND_DUELS"]
        df["ground_duel_win_pct"] = np.where(total_gd > 0, df["WON_GROUND_DUELS"] / total_gd * 100, np.nan)
    if {"WON_GROUND_DUELS", "LOST_GROUND_DUELS", "WON_AERIAL_DUELS", "LOST_AERIAL_DUELS"}.issubset(df.columns):
        won_duels = df["WON_GROUND_DUELS"] + df["WON_AERIAL_DUELS"]
        total_duels = won_duels + df["LOST_GROUND_DUELS"] + df["LOST_AERIAL_DUELS"]
        df["duel_success_pct"] = np.where(total_duels > 0, won_duels / total_duels * 100, np.nan)
    if {"SUCCESSFUL_PASSES_UNDER_PRESSURE", "PASSES_UNDER_PRESSURE"}.issubset(df.columns):
        df["pass_under_pressure_pct"] = np.where(
            df["PASSES_UNDER_PRESSURE"] > 0,
            df["SUCCESSFUL_PASSES_UNDER_PRESSURE"] / df["PASSES_UNDER_PRESSURE"] * 100,
            np.nan,
        )
    return df.copy()


@st.cache_data(show_spinner=False)
def load_physical() -> pd.DataFrame:
    path = DATA_DIR / "physical.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


@st.cache_data(show_spinner=False)
def load_events() -> pd.DataFrame:
    path = DATA_DIR / "events.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def data_status() -> dict:
    """Short report on what was loaded successfully - shown on the home page."""
    pms, phys, ev = load_playermatchstats(), load_physical(), load_events()
    return {
        "playermatchstats": {"ok": not pms.empty, "rows": len(pms), "cols": pms.shape[1] if not pms.empty else 0},
        "physical": {"ok": not phys.empty, "rows": len(phys), "cols": phys.shape[1] if not phys.empty else 0},
        "events": {"ok": not ev.empty, "rows": len(ev), "cols": ev.shape[1] if not ev.empty else 0},
    }


def get_teams(df: pd.DataFrame) -> list:
    if df.empty or "squadName" not in df.columns:
        return []
    return sorted(df["squadName"].dropna().unique().tolist())


def get_players(df: pd.DataFrame, team: str | None = None) -> list:
    if df.empty or "playerName" not in df.columns:
        return []
    sub = df if not team or team == "All teams" else df[df["squadName"] == team]
    return sorted(sub["playerName"].dropna().unique().tolist())


def player_team(df: pd.DataFrame, player_name: str) -> str | None:
    sub = df[df["playerName"] == player_name]
    if sub.empty:
        return None
    return sub.sort_values("dateTime").iloc[-1]["squadName"] if "dateTime" in sub.columns else sub.iloc[-1]["squadName"]


def aggregate_player(df: pd.DataFrame, player_name: str) -> pd.Series:
    """Sums/averages across all matches of a given player in the loaded data."""
    sub = df[df["playerName"] == player_name]
    if sub.empty:
        return pd.Series(dtype=float)
    sum_cols = [c for c in ["GOALS", "ASSISTS", "SUCCESSFUL_PASSES", "UNSUCCESSFUL_PASSES",
                             "SHOT_AT_GOAL_NUMBER", "BALL_WIN_NUMBER", "BALL_LOSS_NUMBER",
                             "OFFENSIVE_TOUCHES", "DEFENSIVE_TOUCHES", "SHOT_XG", "PACKING_XG",
                             "WON_GROUND_DUELS", "LOST_GROUND_DUELS", "WON_AERIAL_DUELS", "LOST_AERIAL_DUELS",
                             "BYPASSED_OPPONENTS", "NUMBER_OF_FOULS", "NUMBER_OF_FOULS_WON"] if c in sub.columns]
    out = sub[sum_cols].sum()
    out["MATCHES"] = len(sub)
    if {"SUCCESSFUL_PASSES", "UNSUCCESSFUL_PASSES"}.issubset(sub.columns):
        tot = out.get("SUCCESSFUL_PASSES", 0) + out.get("UNSUCCESSFUL_PASSES", 0)
        out["pass_accuracy_pct"] = (out["SUCCESSFUL_PASSES"] / tot * 100) if tot > 0 else np.nan
    return out


def zone_grid_from_marginals(pitch_counts: list, lane_counts: list) -> np.ndarray:
    """
    Builds an approximate 5x5 grid (zone x lane) from TWO independent marginal
    distributions (because the playermatchstats data reports them separately,
    not as a single joint cross-table). We assume independence of both
    dimensions - this is an approximation, not the exact joint distribution,
    and this is noted as such in the UI.
    """
    pitch = np.array(pitch_counts, dtype=float)
    lane = np.array(lane_counts, dtype=float)
    total = pitch.sum()
    if total <= 0 or lane.sum() <= 0:
        return np.zeros((5, 5))
    pitch_p = pitch / pitch.sum()
    lane_p = lane / lane.sum()
    grid = np.outer(lane_p, pitch_p) * total
    return grid
