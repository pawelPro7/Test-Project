"""
Demo data generator for the Football Analytics app.

IMPORTANT:
- The only real data row (Phil Neumann / Birmingham City, matchId 206530)
  comes directly from the file provided by the user and is copied UNCHANGED
  into the final playermatchstats.csv.
- All other rows (4 fictional teams, fictional players, fictional matches)
  are synthetic and exist solely to demonstrate how the app works. They do
  not represent real clubs or players.
- physical.csv and events.csv were NOT provided in their original structure
  (the user uploaded the same playermatchstats.csv file three times), so the
  schema below is a reasonable, industry-typical assumption (see README.md).
  The app's loader is written defensively, so if you replace these files with
  real exports that use different columns, most views still work (and
  whatever needs specific columns will report it in the UI instead of
  crashing).

Run with:
    python scripts/generate_demo_data.py
"""
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

RNG = np.random.default_rng(42)

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
REAL_PATH = ROOT / "scripts" / "reference_real_row.csv"

# --------------------------------------------------------------------------------------
# 1. Load the real row and column list (to preserve exactly the same schema)
# --------------------------------------------------------------------------------------
real_df = pd.read_csv(REAL_PATH)
ALL_COLUMNS = list(real_df.columns)
REAL_ROW = real_df.iloc[0].to_dict()

# --------------------------------------------------------------------------------------
# 2. Fictional teams and rosters
# --------------------------------------------------------------------------------------
TEAMS = [
    {"squadId": 9001, "squadName": "Northgate FC"},
    {"squadId": 9002, "squadName": "Ashford Athletic"},
    {"squadId": 9003, "squadName": "Meridian United"},
    {"squadId": 9004, "squadName": "Castlebay Rovers"},
]

ROSTERS = {
    9001: [
        dict(playerId=910101, firstname="Adrian", lastname="Voss", birthdate="1994-03-12",
             birthplace="Hamburg", playerCountry="Germany", position="GOALKEEPER", leg="RIGHT"),
        dict(playerId=910102, firstname="Marcus", lastname="Lindqvist", birthdate="1998-06-02",
             birthplace="Malmoe", playerCountry="Sweden", position="CENTRAL_DEFENDER", leg="RIGHT"),
        dict(playerId=910103, firstname="Tomasz", lastname="Wisniewski", birthdate="1999-11-20",
             birthplace="Poznan", playerCountry="Poland", position="CENTRAL_DEFENDER", leg="LEFT"),
        dict(playerId=910104, firstname="Kwabena", lastname="Owusu", birthdate="2000-02-18",
             birthplace="Kumasi", playerCountry="Ghana", position="FULLBACK_RIGHT", leg="RIGHT"),
        dict(playerId=910105, firstname="Noah", lastname="Fischer", birthdate="1997-09-09",
             birthplace="Stuttgart", playerCountry="Germany", position="DEFENSIVE_MIDFIELD", leg="RIGHT"),
        dict(playerId=910106, firstname="Lucas", lastname="Ferreira", birthdate="2001-01-27",
             birthplace="Porto", playerCountry="Portugal", position="WINGER_LEFT", leg="LEFT"),
        dict(playerId=910107, firstname="Erik", lastname="Johansson", birthdate="1996-05-14",
             birthplace="Goeteborg", playerCountry="Sweden", position="CENTER_FORWARD", leg="RIGHT"),
    ],
    9002: [
        dict(playerId=920101, firstname="Ben", lastname="Whitmore", birthdate="1995-08-01",
             birthplace="Leeds", playerCountry="England", position="GOALKEEPER", leg="RIGHT"),
        dict(playerId=920102, firstname="Callum", lastname="Reyes", birthdate="1997-12-11",
             birthplace="Bristol", playerCountry="England", position="CENTRAL_DEFENDER", leg="RIGHT"),
        dict(playerId=920103, firstname="Diego", lastname="Salinas", birthdate="1998-04-23",
             birthplace="Sevilla", playerCountry="Spain", position="CENTRAL_DEFENDER", leg="LEFT"),
        dict(playerId=920104, firstname="Harry", lastname="Nolan", birthdate="2001-07-05",
             birthplace="Coventry", playerCountry="England", position="FULLBACK_RIGHT", leg="RIGHT"),
        dict(playerId=920105, firstname="Youssef", lastname="Amrani", birthdate="1996-10-30",
             birthplace="Fes", playerCountry="Morocco", position="DEFENSIVE_MIDFIELD", leg="RIGHT"),
        dict(playerId=920106, firstname="Jamie", lastname="Elliot", birthdate="2000-03-15",
             birthplace="Newcastle", playerCountry="England", position="WINGER_LEFT", leg="LEFT"),
        dict(playerId=920107, firstname="Theo", lastname="Baptiste", birthdate="1999-01-09",
             birthplace="Lyon", playerCountry="France", position="CENTER_FORWARD", leg="RIGHT"),
    ],
    9003: [
        dict(playerId=930101, firstname="Viktor", lastname="Petrov", birthdate="1993-05-22",
             birthplace="Sofia", playerCountry="Bulgaria", position="GOALKEEPER", leg="RIGHT"),
        dict(playerId=930102, firstname="Milan", lastname="Novak", birthdate="1997-02-14",
             birthplace="Brno", playerCountry="Czechia", position="CENTRAL_DEFENDER", leg="RIGHT"),
        dict(playerId=930103, firstname="Kacper", lastname="Zielinski", birthdate="2000-09-03",
             birthplace="Gdansk", playerCountry="Poland", position="CENTRAL_DEFENDER", leg="RIGHT"),
        dict(playerId=930104, firstname="Rafael", lastname="Costa", birthdate="1999-06-19",
             birthplace="Braga", playerCountry="Portugal", position="FULLBACK_RIGHT", leg="RIGHT"),
        dict(playerId=930105, firstname="Igor", lastname="Marchenko", birthdate="1998-11-27",
             birthplace="Lviv", playerCountry="Ukraine", position="DEFENSIVE_MIDFIELD", leg="LEFT"),
        dict(playerId=930106, firstname="Simon", lastname="Baker", birthdate="2002-01-08",
             birthplace="Nottingham", playerCountry="England", position="WINGER_LEFT", leg="LEFT"),
        dict(playerId=930107, firstname="Aleksander", lastname="Dahl", birthdate="1997-04-17",
             birthplace="Bergen", playerCountry="Norway", position="CENTER_FORWARD", leg="RIGHT"),
    ],
    9004: [
        dict(playerId=940101, firstname="Owen", lastname="Sinclair", birthdate="1996-07-25",
             birthplace="Glasgow", playerCountry="Scotland", position="GOALKEEPER", leg="RIGHT"),
        dict(playerId=940102, firstname="Liam", lastname="Forsythe", birthdate="1998-03-30",
             birthplace="Aberdeen", playerCountry="Scotland", position="CENTRAL_DEFENDER", leg="RIGHT"),
        dict(playerId=940103, firstname="Nikolai", lastname="Sorensen", birthdate="1999-12-05",
             birthplace="Aarhus", playerCountry="Denmark", position="CENTRAL_DEFENDER", leg="LEFT"),
        dict(playerId=940104, firstname="Ryan", lastname="Doherty", birthdate="2000-05-11",
             birthplace="Cork", playerCountry="Ireland", position="FULLBACK_RIGHT", leg="RIGHT"),
        dict(playerId=940105, firstname="Bastian", lastname="Hartmann", birthdate="1995-10-02",
             birthplace="Koeln", playerCountry="Germany", position="DEFENSIVE_MIDFIELD", leg="RIGHT"),
        dict(playerId=940106, firstname="Mateusz", lastname="Kaczmarek", birthdate="2001-08-14",
             birthplace="Wroclaw", playerCountry="Poland", position="WINGER_LEFT", leg="LEFT"),
        dict(playerId=940107, firstname="Gabriel", lastname="Silva", birthdate="1998-02-28",
             birthplace="Porto Alegre", playerCountry="Brazil", position="CENTER_FORWARD", leg="RIGHT"),
    ],
}
for squad_id, roster in ROSTERS.items():
    for p in roster:
        p["playerName"] = f'{p["firstname"]} {p["lastname"]}'
        p["squadId"] = squad_id

TEAM_BY_ID = {t["squadId"]: t["squadName"] for t in TEAMS}

# --------------------------------------------------------------------------------------
# 3. Fixtures (round-robin, 3 matchdays) + shared per-position rates
# --------------------------------------------------------------------------------------
FIXTURES = [
    (1, "2025-08-09T15:00:00Z", 9001, 9002),
    (1, "2025-08-09T17:30:00Z", 9003, 9004),
    (2, "2025-08-16T15:00:00Z", 9001, 9003),
    (2, "2025-08-16T17:30:00Z", 9002, 9004),
    (3, "2025-08-23T15:00:00Z", 9001, 9004),
    (3, "2025-08-23T17:30:00Z", 9002, 9003),
]
COMPETITION_NAME = "Demo League"
COMPETITION_ID = 9999
COMPETITION_TYPE = "League"
ITERATION_ID = 9100
SEASON = "25/26"

# ranges: (min, max) uniform sampling unless noted
POSITION_PROFILE = {
    "GOALKEEPER":          dict(pass_s=(12, 24), pass_u=(1, 5),  off_t=(1, 4),   def_t=(18, 32),
                                 duel=(0, 1), aer=(0, 3), shots=(0, 0), goal_w=0.0,  assist_w=0.0,  pack=(0, 0.1)),
    "CENTRAL_DEFENDER":    dict(pass_s=(28, 58), pass_u=(3, 11), off_t=(14, 30), def_t=(10, 24),
                                 duel=(3, 11), aer=(2, 9), shots=(0, 1), goal_w=0.04, assist_w=0.03, pack=(0, 1.0)),
    "FULLBACK_RIGHT":      dict(pass_s=(24, 50), pass_u=(3, 12), off_t=(18, 36), def_t=(6, 18),
                                 duel=(3, 10), aer=(0, 4), shots=(0, 1), goal_w=0.05, assist_w=0.12, pack=(0.2, 1.8)),
    "DEFENSIVE_MIDFIELD":  dict(pass_s=(32, 64), pass_u=(4, 13), off_t=(22, 42), def_t=(8, 20),
                                 duel=(4, 12), aer=(1, 6), shots=(0, 2), goal_w=0.08, assist_w=0.10, pack=(0.3, 2.2)),
    "WINGER_LEFT":         dict(pass_s=(16, 36), pass_u=(4, 13), off_t=(24, 46), def_t=(1, 8),
                                 duel=(3, 10), aer=(0, 3), shots=(1, 4), goal_w=0.22, assist_w=0.22, pack=(0.6, 3.0)),
    "CENTER_FORWARD":      dict(pass_s=(10, 26), pass_u=(3, 11), off_t=(20, 40), def_t=(1, 6),
                                 duel=(3, 11), aer=(2, 9), shots=(1, 5), goal_w=0.38, assist_w=0.14, pack=(0.5, 2.8)),
}

# share of pitch zones (OWN_BOX, FIRST_THIRD, MIDDLE_THIRD, FINAL_THIRD, OPPONENT_BOX)
PITCH_BIAS_OFF = {
    "GOALKEEPER":         [0.55, 0.35, 0.10, 0.00, 0.00],
    "CENTRAL_DEFENDER":   [0.12, 0.45, 0.32, 0.10, 0.01],
    "FULLBACK_RIGHT":     [0.04, 0.30, 0.36, 0.24, 0.06],
    "DEFENSIVE_MIDFIELD": [0.02, 0.20, 0.46, 0.27, 0.05],
    "WINGER_LEFT":        [0.00, 0.06, 0.26, 0.48, 0.20],
    "CENTER_FORWARD":     [0.00, 0.03, 0.17, 0.48, 0.32],
}
# share of lanes (RIGHT_WING, RIGHT_HALF_SPACE, CENTER, LEFT_HALF_SPACE, LEFT_WING)
LANE_BIAS = {
    "GOALKEEPER":         [0.10, 0.20, 0.40, 0.20, 0.10],
    "CENTRAL_DEFENDER":   [0.10, 0.27, 0.28, 0.25, 0.10],
    "FULLBACK_RIGHT":     [0.55, 0.25, 0.06, 0.09, 0.05],
    "DEFENSIVE_MIDFIELD": [0.12, 0.24, 0.30, 0.22, 0.12],
    "WINGER_LEFT":        [0.05, 0.08, 0.14, 0.25, 0.48],
    "CENTER_FORWARD":     [0.16, 0.20, 0.30, 0.19, 0.15],
}
PITCH_BIAS_DEF = {
    "GOALKEEPER":         [0.60, 0.32, 0.08, 0.00, 0.00],
    "CENTRAL_DEFENDER":   [0.28, 0.44, 0.24, 0.04, 0.00],
    "FULLBACK_RIGHT":     [0.16, 0.42, 0.32, 0.09, 0.01],
    "DEFENSIVE_MIDFIELD": [0.08, 0.34, 0.44, 0.13, 0.01],
    "WINGER_LEFT":        [0.02, 0.14, 0.42, 0.32, 0.10],
    "CENTER_FORWARD":     [0.01, 0.09, 0.40, 0.35, 0.15],
}
ZONE_ORDER = ["OWN_BOX", "FIRST_THIRD", "MIDDLE_THIRD", "FINAL_THIRD", "OPPONENT_BOX"]
LANE_ORDER = ["RIGHT_WING", "RIGHT_HALF_SPACE", "CENTER", "LEFT_HALF_SPACE", "LEFT_WING"]

ATTACK_WEIGHT = {  # weight for probability of scoring a goal / assist
    "GOALKEEPER": 0.01, "CENTRAL_DEFENDER": 1.0, "FULLBACK_RIGHT": 1.4,
    "DEFENSIVE_MIDFIELD": 1.6, "WINGER_LEFT": 3.2, "CENTER_FORWARD": 4.2,
}


def blank_row():
    row = {c: 0 for c in ALL_COLUMNS}
    return row


def sample_zone_counts(total, bias):
    if total <= 0:
        return [0] * 5
    probs = np.array(bias, dtype=float)
    probs = probs / probs.sum()
    return list(RNG.multinomial(int(round(total)), probs))


def age_from_birthdate(bdate_str, at_date):
    b = datetime.strptime(bdate_str, "%Y-%m-%d")
    return (at_date - b).days // 365


rows_pms, rows_phys, rows_events = [], [], []
event_id_counter = 1

for md_idx, dt_str, home_id, away_id in FIXTURES:
    match_id = 900000 + md_idx * 10 + home_id % 10 + away_id % 10  # unique, deterministic
    match_dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%SZ")
    md_name = f"{COMPETITION_NAME} - matchday {md_idx}"

    home_goals = int(np.clip(RNG.poisson(1.35), 0, 5))
    away_goals = int(np.clip(RNG.poisson(1.1), 0, 5))

    for team_id, opp_goals, own_goals in [(home_id, away_goals, home_goals), (away_id, home_goals, away_goals)]:
        roster = ROSTERS[team_id]
        squad_name = TEAM_BY_ID[team_id]

        # -- who played how many minutes --
        player_state = []
        for p in roster:
            starts_full = RNG.random() > 0.18
            share = 1.0 if starts_full else round(float(RNG.uniform(0.15, 0.65)), 2)
            player_state.append({**p, "matchShare": share})

        # -- distributing goals/assists in this match for this team --
        goals_count = {p["playerId"]: 0 for p in player_state}
        assists_count = {p["playerId"]: 0 for p in player_state}
        weights = np.array([ATTACK_WEIGHT[p["position"]] for p in player_state], dtype=float)
        weights = weights / weights.sum()
        scorers_idx = RNG.choice(len(player_state), size=own_goals, p=weights) if own_goals > 0 else []
        for si in scorers_idx:
            goals_count[player_state[si]["playerId"]] += 1
            if RNG.random() < 0.65:
                candidates = [i for i in range(len(player_state)) if i != si and player_state[i]["position"] != "GOALKEEPER"]
                if candidates:
                    aw = np.array([ATTACK_WEIGHT[player_state[i]["position"]] for i in candidates], dtype=float)
                    aw = aw / aw.sum()
                    ai = RNG.choice(candidates, p=aw)
                    assists_count[player_state[ai]["playerId"]] += 1

        for p in player_state:
            pos = p["position"]
            prof = POSITION_PROFILE[pos]
            share = p["matchShare"]
            scale = max(share, 0.12)

            row = blank_row()
            row.update({
                "matchId": match_id, "dateTime": dt_str, "competitionName": COMPETITION_NAME,
                "competitionId": COMPETITION_ID, "competitionType": COMPETITION_TYPE,
                "iterationId": ITERATION_ID, "season": SEASON, "matchDayIndex": md_idx,
                "matchDayName": md_name, "squadId": team_id, "squadName": squad_name,
                "playerId": p["playerId"], "wyscoutId": p["playerId"] + 500000,
                "skillCornerId": p["playerId"] + 20000, "heimSpielId": p["playerId"] + 700000,
                "playerName": p["playerName"], "firstname": p["firstname"], "lastname": p["lastname"],
                "birthdate": p["birthdate"], "birthplace": p["birthplace"], "playerCountry": p["playerCountry"],
                "leg": p["leg"], "position": pos, "matchShare": share,
            })

            pass_s = int(RNG.uniform(*prof["pass_s"]) * scale)
            pass_u = int(RNG.uniform(*prof["pass_u"]) * scale)
            off_t = int(RNG.uniform(*prof["off_t"]) * scale)
            def_t = int(RNG.uniform(*prof["def_t"]) * scale)
            won_gd = int(RNG.uniform(*prof["duel"]) * scale)
            lost_gd = int(RNG.uniform(0, prof["duel"][1]) * scale)
            won_ad = int(RNG.uniform(0, prof["aer"][1]) * scale)
            lost_ad = int(RNG.uniform(0, prof["aer"][1]) * scale * 0.8)
            shots = int(round(RNG.uniform(*prof["shots"]) * scale))
            goals = goals_count[p["playerId"]]
            assists = assists_count[p["playerId"]]
            shots = max(shots, goals)  # whoever scored a goal must have taken >=1 shot
            packing_xg = round(float(RNG.uniform(*prof["pack"]) * scale), 2)
            shot_xg = round(float(max(goals * RNG.uniform(0.28, 0.75), RNG.uniform(0, 0.45) if shots else 0) * scale), 3)
            ball_win = int(RNG.uniform(2, 16) * scale)
            ball_loss = int(RNG.uniform(2, 16) * scale)
            fouls = int(RNG.uniform(0, 3) * scale)
            fouls_won = int(RNG.uniform(0, 3) * scale)
            offside = int(RNG.uniform(0, 1) * scale) if pos in ("WINGER_LEFT", "CENTER_FORWARD") else 0
            bypassed_opp = round(float(off_t * RNG.uniform(0.2, 0.6)), 1)
            bypassed_def = round(float(bypassed_opp * RNG.uniform(0.15, 0.4)), 1)
            playduration = round(share * RNG.uniform(5400, 6100), 2)

            off_zone = sample_zone_counts(off_t, PITCH_BIAS_OFF[pos])
            off_lane = sample_zone_counts(off_t, LANE_BIAS[pos])
            def_zone = sample_zone_counts(def_t, PITCH_BIAS_DEF[pos])
            bypassed_zone = sample_zone_counts(bypassed_opp, PITCH_BIAS_OFF[pos])
            bypassed_lane = sample_zone_counts(bypassed_opp, LANE_BIAS[pos])
            ballwin_zone = sample_zone_counts(ball_win, PITCH_BIAS_DEF[pos])
            ballwin_lane = sample_zone_counts(ball_win, LANE_BIAS[pos])

            row.update({
                "GOALS": goals, "ASSISTS": assists, "OWNGOALS": 0, "RED_CARD": 0,
                "OPPONENT_GOALS": opp_goals, "CONCEDED_GOALS": opp_goals,
                "CONCEDED_SHOT_XG": round(float(opp_goals * 0.55 + RNG.uniform(0.3, 1.4)), 2),
                "CONCEDED_POSTSHOT_XG": round(float(opp_goals * 0.6 + RNG.uniform(0.2, 1.1)), 2),
                "SHOT_XG": shot_xg, "PACKING_XG": packing_xg,
                "POSTSHOT_XG": round(shot_xg * RNG.uniform(0.8, 1.3), 3) if shots else 0,
                "SUCCESSFUL_PASSES": pass_s, "UNSUCCESSFUL_PASSES": pass_u,
                "OFFENSIVE_TOUCHES": off_t, "DEFENSIVE_TOUCHES": def_t,
                "WON_GROUND_DUELS": won_gd, "LOST_GROUND_DUELS": lost_gd,
                "WON_AERIAL_DUELS": won_ad, "LOST_AERIAL_DUELS": lost_ad,
                "SHOT_AT_GOAL_NUMBER": shots, "SHOT_AT_GOAL_OFF_TARGET_NUMBER": max(shots - goals - int(RNG.uniform(0, 2)), 0),
                "SHOT_AT_GOAL_NUMBER_ON_TARGET": min(goals + int(RNG.uniform(0, max(shots - goals, 0) + 1)), shots),
                "SHOT_AT_GOAL_NUMBER_SUCCESS": goals,
                "BALL_WIN_NUMBER": ball_win, "BALL_LOSS_NUMBER": ball_loss,
                "CRITICAL_BALL_LOSS_NUMBER": int(RNG.uniform(0, 2) * scale),
                "NUMBER_OF_FOULS": fouls, "NUMBER_OF_FOULS_WON": fouls_won,
                "NUMBER_OF_PENALTIES_WON": 0, "NUMBER_OF_OFFSIDES": offside,
                "BYPASSED_OPPONENTS": bypassed_opp, "BYPASSED_DEFENDERS": bypassed_def,
                "BYPASSED_OPPONENTS_NUMBER": int(off_t * RNG.uniform(0.1, 0.3)),
                "PLAYDURATION": playduration, "EFFECTIVE_PLAYDURATION": round(playduration * 0.94, 2),
                "BALL_IN_PLAY_TIME": round(playduration * 0.75, 2),
                "PXT_PASS": round(float(RNG.normal(0.02, 0.03) * scale), 5),
                "PXT_DRIBBLE": round(float(RNG.normal(0.005, 0.015) * scale), 5),
                "PXT_BALL_WIN": round(float(RNG.normal(0.005, 0.01) * scale), 5),
                "PXT_SETPIECE": round(float(RNG.normal(0.0, 0.008) * scale), 5),
                "PXT_SHOT": round(float(shot_xg * RNG.uniform(0.05, 0.2)), 5),
                "PXT_FOUL": round(float(RNG.normal(-0.001, 0.003) * scale), 5),
                "PXT_REC": round(float(RNG.normal(0.002, 0.006) * scale), 5),
                "DEF_PXT_BALL_WIN": round(float(RNG.normal(-0.01, 0.02) * scale), 5),
                "DEF_PXT_PASS": round(float(RNG.normal(0.0, 0.01) * scale), 5),
                "SHOT_CREATING_ACTIONS": int(RNG.uniform(0, 4) * scale) + assists,
                "PRE_ASSISTS": int(RNG.uniform(0, 3) * scale),
                "SHOT_ASSISTS": assists + int(RNG.uniform(0, 2) * scale),
                "EXPECTED_SHOT_ASSISTS": round(float(RNG.uniform(0, 0.3) * scale), 3),
                "EXPECTED_GOAL_ASSISTS": round(float(assists * RNG.uniform(0.2, 0.5)), 3),
                "EXPECTED_PASSES": round(float((pass_s + pass_u) * RNG.uniform(0.92, 1.05)), 2),
                "DRIBBLE_CARRY": int(RNG.uniform(2, 20) * scale),
                "DRIBBLE_ONE_VS_ONE": int(RNG.uniform(0, 4) * scale),
                "DRIBBLE_ONE_VS_ONE_SUCCESS": 0,
                "DRIBBLE_ESCAPE_PRESSURE": int(RNG.uniform(0, 6) * scale),
                "DRIBBLE_STEPPING_IN": int(RNG.uniform(0, 3) * scale),
                "DRIBBLE_PROGRESSIVE_CARRY": int(RNG.uniform(0, 5) * scale),
                "NUMBER_OF_PRESSES": int(RNG.uniform(2, 18) * scale),
                "NUMBER_OF_PRESSES_COUNTER_PRESS": int(RNG.uniform(0, 6) * scale),
                "NUMBER_OF_PRESSURES_EVENT": int(RNG.uniform(2, 20) * scale),
                "NUMBER_OF_PRESSURES_EVENT_FINAL_THIRD": int(RNG.uniform(0, 6) * scale),
                "WON_GROUND_DUELS_DEF": int(won_gd * 0.6), "WON_GROUND_DUELS_OFF": int(won_gd * 0.4),
                "LOST_GROUND_DUELS_DEF": int(lost_gd * 0.6), "LOST_GROUND_DUELS_OFF": int(lost_gd * 0.4),
                "WON_AERIAL_DUELS_DEF": int(won_ad * 0.6), "WON_AERIAL_DUELS_OFF": int(won_ad * 0.4),
                "LOST_AERIAL_DUELS_DEF": int(lost_ad * 0.6), "LOST_AERIAL_DUELS_OFF": int(lost_ad * 0.4),
                "LEFT_FOOT": int((off_t + def_t) * (0.75 if p["leg"] == "LEFT" else 0.25)),
                "RIGHT_FOOT": int((off_t + def_t) * (0.75 if p["leg"] == "RIGHT" else 0.25)),
            })
            for i, zone in enumerate(ZONE_ORDER):
                row[f"OFFENSIVE_TOUCHES_IN_PITCH_POSITION_{zone}"] = int(off_zone[i])
                row[f"DEFENSIVE_TOUCHES_IN_PITCH_POSITION_{zone}"] = int(def_zone[i])
                row[f"BYPASSED_OPPONENTS_FROM_PITCH_POSITION_{zone}"] = round(float(bypassed_zone[i]), 1)
                row[f"BALL_WIN_NUMBER_FROM_PITCH_POSITION_{zone}"] = int(ballwin_zone[i])
            for i, lane in enumerate(LANE_ORDER):
                row[f"OFFENSIVE_TOUCHES_IN_LANE_{lane}"] = int(off_lane[i])
                row[f"BYPASSED_OPPONENTS_FROM_LANE_{lane}"] = round(float(bypassed_lane[i]), 1)
                row[f"BALL_WIN_NUMBER_IN_LANE_{lane}"] = int(ballwin_lane[i])

            if pos == "GOALKEEPER":
                box_faced = int(RNG.uniform(4, 14) * scale)
                row.update({
                    "box_deliveries_faced": box_faced,
                    "claims": int(RNG.uniform(0, min(box_faced, 4))),
                    "gk_catches": int(RNG.uniform(0, 6) * scale),
                    "gk_punch_parry": int(RNG.uniform(0, 4) * scale),
                    "expected_claims": round(float(box_faced * RNG.uniform(0.2, 0.45)), 2),
                    "SHOT_AT_GOAL_NUMBER_SAVED": int(RNG.uniform(0, 5)),
                })

            rows_pms.append(row)

            # ---------------- physical.csv ----------------
            minutes = round(share * RNG.uniform(88, 98), 1)
            base_distance = {"GOALKEEPER": 4200, "CENTRAL_DEFENDER": 9200, "FULLBACK_RIGHT": 10800,
                              "DEFENSIVE_MIDFIELD": 11200, "WINGER_LEFT": 10600, "CENTER_FORWARD": 9800}[pos]
            total_distance = round(base_distance * scale * RNG.uniform(0.9, 1.1), 0)
            hsr = round(total_distance * RNG.uniform(0.05, 0.16), 0)
            sprint_dist = round(hsr * RNG.uniform(0.25, 0.55), 0)
            rows_phys.append({
                "matchId": match_id, "dateTime": dt_str, "competitionName": COMPETITION_NAME,
                "season": SEASON, "matchDayIndex": md_idx, "squadId": team_id, "squadName": squad_name,
                "playerId": p["playerId"], "playerName": p["playerName"], "position": pos,
                "minutesPlayed": minutes, "totalDistanceM": total_distance,
                "distancePer90M": round(total_distance / max(minutes, 1) * 90, 0),
                "hsrDistanceM": hsr, "sprintDistanceM": sprint_dist,
                "numSprints": int(sprint_dist / RNG.uniform(14, 20)),
                "topSpeedKmh": round(float(RNG.uniform(24, 34) if pos != "GOALKEEPER" else RNG.uniform(18, 24)), 1),
                "accelerations": int(RNG.uniform(10, 40) * scale),
                "decelerations": int(RNG.uniform(10, 40) * scale),
                "distanceInPossessionM": round(total_distance * RNG.uniform(0.35, 0.5), 0),
                "distanceOutOfPossessionM": round(total_distance * RNG.uniform(0.5, 0.65), 0),
            })

            # ---------------- events.csv ----------------
            n_events = int(RNG.uniform(4, 16) * scale) + (2 if pos != "GOALKEEPER" else 0)
            pitch_p = np.array(PITCH_BIAS_OFF[pos]) / np.sum(PITCH_BIAS_OFF[pos])
            lane_p = np.array(LANE_BIAS[pos]) / np.sum(LANE_BIAS[pos])
            x_bins = [(0, 6), (6, 33), (33, 66), (66, 94), (94, 100)]
            y_bins = [(0, 20), (20, 37), (37, 63), (63, 80), (80, 100)]
            ev_types = RNG.choice(
                ["PASS", "PASS", "PASS", "DUEL", "TACKLE", "INTERCEPTION", "DRIBBLE", "CROSS", "CLEARANCE"],
                size=n_events)
            if shots > 0:
                ev_types = np.concatenate([ev_types, np.array(["SHOT"] * shots)])
            for et in ev_types:
                zi = RNG.choice(5, p=pitch_p)
                li = RNG.choice(5, p=lane_p)
                if et == "SHOT":
                    zi = 4 if RNG.random() < 0.65 else 3
                x = round(float(RNG.uniform(*x_bins[zi])), 1)
                y = round(float(RNG.uniform(*y_bins[li])), 1)
                success = 1 if RNG.random() < (0.85 if et == "PASS" else 0.55) else 0
                end_x = round(float(np.clip(x + RNG.uniform(-5, 20), 0, 100)), 1) if et in ("PASS", "CROSS", "DRIBBLE") else None
                end_y = round(float(np.clip(y + RNG.uniform(-15, 15), 0, 100)), 1) if et in ("PASS", "CROSS", "DRIBBLE") else None
                xg_val = round(float(np.clip(RNG.uniform(0.02, 0.5) * (1.4 if x > 88 else 1.0), 0.01, 0.95)), 3) if et == "SHOT" else None
                rows_events.append({
                    "matchId": match_id, "eventId": event_id_counter, "dateTime": dt_str,
                    "minute": int(RNG.uniform(1, 90)), "second": int(RNG.uniform(0, 59)),
                    "half": 1 if RNG.random() < 0.5 else 2,
                    "squadId": team_id, "squadName": squad_name,
                    "playerId": p["playerId"], "playerName": p["playerName"],
                    "eventType": et, "outcome": "SUCCESSFUL" if success else "UNSUCCESSFUL",
                    "x": x, "y": y, "endX": end_x, "endY": end_y, "xG": xg_val,
                })
                event_id_counter += 1

# --------------------------------------------------------------------------------------
# 4. Save files (real row + synthetic, in that order)
# --------------------------------------------------------------------------------------
pms_df = pd.concat([pd.DataFrame([REAL_ROW]), pd.DataFrame(rows_pms)], ignore_index=True)
pms_df = pms_df[ALL_COLUMNS]
pms_df.to_csv(DATA_DIR / "playermatchstats.csv", index=False)

phys_df = pd.DataFrame(rows_phys)
phys_df.to_csv(DATA_DIR / "physical.csv", index=False)

events_df = pd.DataFrame(rows_events)
events_df.to_csv(DATA_DIR / "events.csv", index=False)

print(f"playermatchstats.csv -> {pms_df.shape[0]} rows, {pms_df.shape[1]} columns")
print(f"physical.csv         -> {phys_df.shape[0]} rows, {phys_df.shape[1]} columns")
print(f"events.csv           -> {events_df.shape[0]} rows, {events_df.shape[1]} columns")
