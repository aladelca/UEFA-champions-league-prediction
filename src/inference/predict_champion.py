from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

from src.data.load_raw import load_raw_df
from src.simulation.bracket_builder import load_rules_for_season
from src.simulation.monte_carlo import simulate_champion_probs
from src.utils.io import read_dataframe, resolve_existing_data_path


MATCHES_PATH = Path("data/interim/matches_unique.parquet")


def _load_matches_unique() -> pd.DataFrame:
    if resolve_existing_data_path(MATCHES_PATH) is None:
        from src.data.build_matches_unique import main as build_matches_main

        build_matches_main()
    return read_dataframe(MATCHES_PATH, parse_dates=["Date"]).sort_values(["Date", "match_id"])


def _teams_for_season(season: int) -> List[str]:
    matches = _load_matches_unique()
    season_matches = matches[matches["season"] == season]
    if season_matches.empty:
        raise ValueError(f"No matches found for season={season}")
    teams = sorted(set(season_matches["home_team"]).union(set(season_matches["away_team"])))
    if len(teams) != 32:
        raise ValueError(f"Expected 32 teams for season={season}, got {len(teams)}")
    return teams


def _build_preseason_ratings(season: int, teams: list[str]) -> dict[str, float]:
    matches = _load_matches_unique()
    hist = matches[matches["season"] < season].copy()

    points: dict[str, float] = {team: 0.0 for team in teams}
    played: dict[str, int] = {team: 0 for team in teams}

    for _, row in hist.iterrows():
        home = str(row["home_team"])
        away = str(row["away_team"])
        hg = int(row["home_goals"])
        ag = int(row["away_goals"])

        if home not in points:
            points[home] = 0.0
            played[home] = 0
        if away not in points:
            points[away] = 0.0
            played[away] = 0

        if hg > ag:
            points[home] += 3.0
        elif hg < ag:
            points[away] += 3.0
        else:
            points[home] += 1.0
            points[away] += 1.0

        played[home] += 1
        played[away] += 1

    ratings: dict[str, float] = {}
    for team in teams:
        p = points.get(team, 0.0)
        m = played.get(team, 0)
        if m == 0:
            ratings[team] = 1500.0
            continue
        ppg = p / m
        rating = 1500.0 + 200.0 * (ppg - 1.35)
        ratings[team] = float(np.clip(rating, 1300.0, 1900.0))

    return ratings


def simulate_season_from_start(season: int, n_simulations: int, random_seed: int = 42) -> Dict:
    teams = _teams_for_season(season)
    ratings = _build_preseason_ratings(season, teams)
    rules = load_rules_for_season(season)

    probs = simulate_champion_probs(
        teams=teams,
        ratings=ratings,
        rules=rules,
        n_simulations=n_simulations,
        random_seed=random_seed,
    )

    ranked = sorted(probs.items(), key=lambda item: item[1], reverse=True)
    results = [
        {"team": team, "p_champion": round(float(prob), 6), "rank": idx + 1}
        for idx, (team, prob) in enumerate(ranked)
    ]
    return {
        "season": season,
        "n_simulations": n_simulations,
        "results": results,
    }
