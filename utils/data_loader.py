"""
Wczytywanie i przygotowywanie danych dla aplikacji.

playermatchstats.csv ma potwierdzony, dokladny schemat (zweryfikowany na proбce
dostarczonej przez uzytkownika), wiec odwolujemy sie do jego kolumn wprost.

physical.csv i events.csv NIE mialy potwierdzonego schematu w momencie budowy tej
aplikacji (uzytkownik przeslal ten sam plik trzykrotnie), wiec kazdy dostep do ich
kolumn przechodzi przez find_column() - elastyczny, nieczuly na wielkosc liter
"dopasowywacz" kolumn. Jesli podmienisz te pliki na realne eksporty o innych
nazwach kolumn, wystarczy rozszerzyc listy kandydatow ponizej (sekcja
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
    "OWN_BOX": "Wlasne pole karne", "FIRST_THIRD": "Pierwsza tercja",
    "MIDDLE_THIRD": "Srodkowa tercja", "FINAL_THIRD": "Ostatnia tercja",
    "OPPONENT_BOX": "Pole karne rywala",
}
LANE_ORDER = ["RIGHT_WING", "RIGHT_HALF_SPACE", "CENTER", "LEFT_HALF_SPACE", "LEFT_WING"]
LANE_LABELS_PL = {
    "RIGHT_WING": "Prawe skrzydlo", "RIGHT_HALF_SPACE": "Prawy polkanal",
    "CENTER": "Srodek", "LEFT_HALF_SPACE": "Lewy polkanal", "LEFT_WING": "Lewe skrzydlo",
}

POSITION_LABELS_PL = {
    "GOALKEEPER": "Bramkarz", "CENTRAL_DEFENDER": "Srodkowy obronca",
    "FULLBACK_RIGHT": "Prawy obronca", "FULLBACK_LEFT": "Lewy obronca",
    "DEFENSIVE_MIDFIELD": "Defensywny pomocnik", "CENTRAL_MIDFIELD": "Srodkowy pomocnik",
    "ATTACKING_MIDFIELD": "Ofensywny pomocnik", "WINGER_RIGHT": "Prawy skrzydlowy",
    "WINGER_LEFT": "Lewy skrzydlowy", "CENTER_FORWARD": "Napastnik",
}

# Kluczowe metryki uzywane w interfejsie: etykieta PL -> nazwa kolumny w danych.
METRIC_LABELS = {
    "Gole": "GOALS",
    "Asysty": "ASSISTS",
    "xG (Shot xG)": "SHOT_XG",
    "Packing xG": "PACKING_XG",
    "Podania celne": "SUCCESSFUL_PASSES",
    "Podania niecelne": "UNSUCCESSFUL_PASSES",
    "Dotkniecia ofensywne": "OFFENSIVE_TOUCHES",
    "Dotkniecia defensywne": "DEFENSIVE_TOUCHES",
    "Wygrane pojedynki (grunt)": "WON_GROUND_DUELS",
    "Przegrane pojedynki (grunt)": "LOST_GROUND_DUELS",
    "Wygrane pojedynki (powietrze)": "WON_AERIAL_DUELS",
    "Przegrane pojedynki (powietrze)": "LOST_AERIAL_DUELS",
    "Strzaly": "SHOT_AT_GOAL_NUMBER",
    "Odzyskane pilki": "BALL_WIN_NUMBER",
    "Stracone pilki": "BALL_LOSS_NUMBER",
    "Ominieci rywale (packing)": "BYPASSED_OPPONENTS",
    "Ominieci obroncy (packing)": "BYPASSED_DEFENDERS",
    "PXT - podania": "PXT_PASS",
    "PXT - drybling": "PXT_DRIBBLE",
    "PXT - odbior": "PXT_BALL_WIN",
    "Faule": "NUMBER_OF_FOULS",
    "Wymuszone faule": "NUMBER_OF_FOULS_WON",
    "Akcje strzelone/asystowane (SCA)": "SHOT_CREATING_ACTIONS",
    "Drybling (udany przewoz)": "DRIBBLE_CARRY",
}

PHYSICAL_COLUMN_CANDIDATES = {
    "matchId": ["matchId", "match_id"],
    "playerId": ["playerId", "player_id"],
    "playerName": ["playerName", "player_name", "name"],
    "squadId": ["squadId", "squad_id", "teamId", "team_id"],
    "squadName": ["squadName", "squad_name", "teamName", "team_name"],
    "position": ["position"],
    "minutesPlayed": ["minutesPlayed", "minutes_played", "minutes"],
    "totalDistanceM": ["totalDistanceM", "total_distance", "distance", "totalDistance"],
    "distancePer90M": ["distancePer90M", "distance_per_90"],
    "hsrDistanceM": ["hsrDistanceM", "hsr_distance", "highSpeedRunningDistance"],
    "sprintDistanceM": ["sprintDistanceM", "sprint_distance"],
    "numSprints": ["numSprints", "num_sprints", "sprints"],
    "topSpeedKmh": ["topSpeedKmh", "top_speed", "maxSpeed"],
    "accelerations": ["accelerations", "num_accelerations"],
    "decelerations": ["decelerations", "num_decelerations"],
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
    """Nieczule na wielkosc liter dopasowanie pierwszej pasujacej kolumny z listy kandydatow."""
    if df is None or df.empty:
        return None
    lower_map = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in lower_map:
            return lower_map[cand.lower()]
    return None


def resolve_columns(df: pd.DataFrame, candidates_map: dict) -> dict:
    """Zwraca {klucz_logiczny: nazwa_kolumny_w_df albo None} dla calej mapy kandydatow."""
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
    """Krotki raport o tym, co udalo sie wczytac - pokazywany na stronie glownej."""
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
    sub = df if not team or team == "Wszystkie drużyny" else df[df["squadName"] == team]
    return sorted(sub["playerName"].dropna().unique().tolist())


def player_team(df: pd.DataFrame, player_name: str) -> str | None:
    sub = df[df["playerName"] == player_name]
    if sub.empty:
        return None
    return sub.sort_values("dateTime").iloc[-1]["squadName"] if "dateTime" in sub.columns else sub.iloc[-1]["squadName"]


def aggregate_player(df: pd.DataFrame, player_name: str) -> pd.Series:
    """Sumy/srednie dla wszystkich meczow danego zawodnika w zaladowanych danych."""
    sub = df[df["playerName"] == player_name]
    if sub.empty:
        return pd.Series(dtype=float)
    sum_cols = [c for c in ["GOALS", "ASSISTS", "SUCCESSFUL_PASSES", "UNSUCCESSFUL_PASSES",
                             "SHOT_AT_GOAL_NUMBER", "BALL_WIN_NUMBER", "BALL_LOSS_NUMBER",
                             "OFFENSIVE_TOUCHES", "DEFENSIVE_TOUCHES", "SHOT_XG", "PACKING_XG",
                             "WON_GROUND_DUELS", "LOST_GROUND_DUELS", "WON_AERIAL_DUELS", "LOST_AERIAL_DUELS",
                             "BYPASSED_OPPONENTS", "NUMBER_OF_FOULS", "NUMBER_OF_FOULS_WON"] if c in sub.columns]
    out = sub[sum_cols].sum()
    out["MECZE"] = len(sub)
    if {"SUCCESSFUL_PASSES", "UNSUCCESSFUL_PASSES"}.issubset(sub.columns):
        tot = out.get("SUCCESSFUL_PASSES", 0) + out.get("UNSUCCESSFUL_PASSES", 0)
        out["pass_accuracy_pct"] = (out["SUCCESSFUL_PASSES"] / tot * 100) if tot > 0 else np.nan
    return out


def zone_grid_from_marginals(pitch_counts: list, lane_counts: list) -> np.ndarray:
    """
    Buduje przyblizona siatke 5x5 (strefa x korytarz) na podstawie DWOCH niezaleznych
    rozkladow brzegowych (bo dane playermatchstats raportuja je osobno, a nie jako
    jedna wspolna tabele krzyzowa). Zakladamy niezaleznosc obu wymiarow - to przyblizenie,
    nie dokladny rozklad wspolny, i tak jest to zaznaczone w interfejsie.
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
