from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import DefaultDict

import pandas as pd

from src.features.elo import EloConfig, expected_score
from src.utils.io import read_dataframe, resolve_existing_data_path, write_dataframe


INTERIM_DIR = Path("data/interim")
MATCHES_PATH = INTERIM_DIR / "matches_unique.parquet"
OUT_PATH = INTERIM_DIR / "feature_store_pre_match.parquet"


def _sum_last_n(history: list[dict], key: str, n: int = 5) -> float:
    if not history:
        return 0.0
    return float(sum(item[key] for item in history[-n:]))


def _sum_all(history: list[dict], key: str) -> float:
    if not history:
        return 0.0
    return float(sum(item[key] for item in history))


def _safe_ppg(points: float, matches: int) -> float:
    return points / matches if matches > 0 else 0.0


def _points_for(gf: int, ga: int) -> int:
    if gf > ga:
        return 3
    if gf == ga:
        return 1
    return 0


def _build_team_feature_prefix(history: list[dict], prefix: str) -> dict:
    matches_before = len(history)
    points_before = _sum_all(history, "points")
    goal_diff_before = _sum_all(history, "gd")
    return {
        f"{prefix}_matches_before": matches_before,
        f"{prefix}_points_before": points_before,
        f"{prefix}_ppg_before": _safe_ppg(points_before, matches_before),
        f"{prefix}_goal_diff_before": goal_diff_before,
        f"{prefix}_points_last5": _sum_last_n(history, "points", n=5),
        f"{prefix}_goal_diff_last5": _sum_last_n(history, "gd", n=5),
    }


def build_feature_store(matches: pd.DataFrame, elo_cfg: EloConfig | None = None) -> pd.DataFrame:
    if elo_cfg is None:
        elo_cfg = EloConfig()

    work = matches.copy()
    work["Date"] = pd.to_datetime(work["Date"], errors="coerce")
    work = work.sort_values(["Date", "match_id"]).reset_index(drop=True)

    elo: DefaultDict[str, float] = defaultdict(lambda: float(elo_cfg.base_rating))
    season_history: DefaultDict[tuple[int, str], list[dict]] = defaultdict(list)
    global_history: DefaultDict[str, list[dict]] = defaultdict(list)
    feature_rows: list[dict] = []

    # Guardrail: build all features for a date using only history strictly before that date.
    for match_date, day_group in work.groupby("Date", sort=True):
        pending_updates: list[dict] = []

        for _, row in day_group.iterrows():
            season = int(row["season"])
            home_team = str(row["home_team"])
            away_team = str(row["away_team"])
            home_goals = int(row["home_goals"])
            away_goals = int(row["away_goals"])

            home_season_hist = season_history[(season, home_team)]
            away_season_hist = season_history[(season, away_team)]
            home_global_hist = global_history[home_team]
            away_global_hist = global_history[away_team]

            elo_home = float(elo[home_team])
            elo_away = float(elo[away_team])

            row_features = {
                "match_id": row["match_id"],
                "season": season,
                "Date": match_date,
                "home_team": home_team,
                "away_team": away_team,
                "y_match": int(row["y_match"]),
                "home_flag": 1,
                "elo_home": elo_home,
                "elo_away": elo_away,
                "elo_diff": elo_home - elo_away,
                # Explicit marker to verify no same-day contamination in validations.
                "guardrail_same_day_batch_mode": 1,
            }

            row_features.update(_build_team_feature_prefix(home_season_hist, "season_home"))
            row_features.update(_build_team_feature_prefix(away_season_hist, "season_away"))
            row_features.update(_build_team_feature_prefix(home_global_hist, "global_home"))
            row_features.update(_build_team_feature_prefix(away_global_hist, "global_away"))

            row_features["form_points_home_last5"] = row_features["season_home_points_last5"]
            row_features["form_points_away_last5"] = row_features["season_away_points_last5"]
            row_features["goal_diff_home_last5"] = row_features["season_home_goal_diff_last5"]
            row_features["goal_diff_away_last5"] = row_features["season_away_goal_diff_last5"]

            row_features["season_points_diff_before"] = (
                row_features["season_home_points_before"] - row_features["season_away_points_before"]
            )
            row_features["season_ppg_diff_before"] = (
                row_features["season_home_ppg_before"] - row_features["season_away_ppg_before"]
            )
            row_features["season_goal_diff_diff_before"] = (
                row_features["season_home_goal_diff_before"] - row_features["season_away_goal_diff_before"]
            )
            row_features["form_points_diff_last5"] = (
                row_features["form_points_home_last5"] - row_features["form_points_away_last5"]
            )
            row_features["form_goal_diff_diff_last5"] = (
                row_features["goal_diff_home_last5"] - row_features["goal_diff_away_last5"]
            )

            feature_rows.append(row_features)
            pending_updates.append(
                {
                    "season": season,
                    "home_team": home_team,
                    "away_team": away_team,
                    "home_goals": home_goals,
                    "away_goals": away_goals,
                    "elo_home_pre": elo_home,
                    "elo_away_pre": elo_away,
                }
            )

        # Update histories and ratings only after all rows of this date were featurized.
        for upd in pending_updates:
            season = int(upd["season"])
            home_team = upd["home_team"]
            away_team = upd["away_team"]
            home_goals = int(upd["home_goals"])
            away_goals = int(upd["away_goals"])

            home_points = _points_for(home_goals, away_goals)
            away_points = _points_for(away_goals, home_goals)

            home_entry = {
                "points": home_points,
                "gf": home_goals,
                "ga": away_goals,
                "gd": home_goals - away_goals,
            }
            away_entry = {
                "points": away_points,
                "gf": away_goals,
                "ga": home_goals,
                "gd": away_goals - home_goals,
            }

            season_history[(season, home_team)].append(home_entry)
            season_history[(season, away_team)].append(away_entry)
            global_history[home_team].append(home_entry)
            global_history[away_team].append(away_entry)

            elo_home_pre = float(upd["elo_home_pre"])
            elo_away_pre = float(upd["elo_away_pre"])
            exp_home = expected_score(elo_home_pre, elo_away_pre)
            exp_away = 1.0 - exp_home

            if home_goals > away_goals:
                actual_home = 1.0
            elif home_goals == away_goals:
                actual_home = 0.5
            else:
                actual_home = 0.0
            actual_away = 1.0 - actual_home

            elo[home_team] = elo_home_pre + elo_cfg.k_factor * (actual_home - exp_home)
            elo[away_team] = elo_away_pre + elo_cfg.k_factor * (actual_away - exp_away)

    return pd.DataFrame(feature_rows)


def main() -> None:
    if resolve_existing_data_path(MATCHES_PATH) is None:
        from src.data.build_matches_unique import main as build_matches_main

        build_matches_main()

    matches = read_dataframe(MATCHES_PATH, parse_dates=["Date"])
    features = build_feature_store(matches)
    saved_path = write_dataframe(features, OUT_PATH, index=False)
    print(f"saved={saved_path}")
    print(f"rows={len(features)}")


if __name__ == "__main__":
    main()
