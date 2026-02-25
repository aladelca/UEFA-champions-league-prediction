from __future__ import annotations

import math
from itertools import combinations
from typing import Any

import numpy as np


def _match_probabilities(
    rating_home: float, rating_away: float, neutral: bool = False, home_advantage: float = 55.0
) -> tuple[float, float, float]:
    effective_home = rating_home + (0.0 if neutral else home_advantage)
    x = (effective_home - rating_away) / 220.0
    p_home_vs_away = 1.0 / (1.0 + math.exp(-x))

    p_draw = max(0.14, 0.27 - min(abs(x) * 0.06, 0.11))
    mass = 1.0 - p_draw
    p_home = mass * p_home_vs_away
    p_away = mass * (1.0 - p_home_vs_away)
    return p_home, p_draw, p_away


def _sample_score(
    rng: np.random.Generator, rating_home: float, rating_away: float, neutral: bool = False
) -> tuple[int, int]:
    p_home, p_draw, p_away = _match_probabilities(rating_home, rating_away, neutral=neutral)
    outcome = rng.choice(["H", "D", "A"], p=[p_home, p_draw, p_away])

    if outcome == "H":
        home_goals = int(rng.integers(1, 4))
        away_goals = int(rng.integers(0, max(home_goals, 1)))
        if home_goals <= away_goals:
            away_goals = max(0, home_goals - 1)
    elif outcome == "A":
        away_goals = int(rng.integers(1, 4))
        home_goals = int(rng.integers(0, max(away_goals, 1)))
        if away_goals <= home_goals:
            home_goals = max(0, away_goals - 1)
    else:
        draw_goals = int(rng.choice([0, 1, 2], p=[0.42, 0.46, 0.12]))
        home_goals = draw_goals
        away_goals = draw_goals
    return home_goals, away_goals


def _resolve_knockout_tie(
    rng: np.random.Generator, team_a: str, team_b: str, ratings: dict[str, float]
) -> str:
    ra = float(ratings.get(team_a, 1500.0))
    rb = float(ratings.get(team_b, 1500.0))
    pa, _, pb = _match_probabilities(ra, rb, neutral=True, home_advantage=0.0)
    return str(rng.choice([team_a, team_b], p=[pa / (pa + pb), pb / (pa + pb)]))


def _play_two_legged_tie(
    rng: np.random.Generator,
    team_a: str,
    team_b: str,
    ratings: dict[str, float],
    away_goals_rule: bool,
) -> str:
    # Leg 1: team_a home
    a1, b1 = _sample_score(rng, ratings[team_a], ratings[team_b], neutral=False)
    # Leg 2: team_b home
    b2, a2 = _sample_score(rng, ratings[team_b], ratings[team_a], neutral=False)

    agg_a = a1 + a2
    agg_b = b1 + b2

    if agg_a > agg_b:
        return team_a
    if agg_b > agg_a:
        return team_b

    if away_goals_rule:
        away_a = a2
        away_b = b1
        if away_a > away_b:
            return team_a
        if away_b > away_a:
            return team_b

    return _resolve_knockout_tie(rng, team_a, team_b, ratings)


def _play_one_leg_tie(
    rng: np.random.Generator, team_a: str, team_b: str, ratings: dict[str, float], neutral: bool = True
) -> str:
    a_goals, b_goals = _sample_score(rng, ratings[team_a], ratings[team_b], neutral=neutral)
    if a_goals > b_goals:
        return team_a
    if b_goals > a_goals:
        return team_b
    return _resolve_knockout_tie(rng, team_a, team_b, ratings)


def _rank_group(group_teams: list[str], stats: dict[str, dict], ratings: dict[str, float]) -> list[str]:
    # Tie-breaker: points, goal diff, goals for, preseason rating.
    return sorted(
        group_teams,
        key=lambda t: (
            stats[t]["pts"],
            stats[t]["gd"],
            stats[t]["gf"],
            ratings.get(t, 1500.0),
        ),
        reverse=True,
    )


def _simulate_group_stage(
    rng: np.random.Generator, groups: list[list[str]], ratings: dict[str, float], rules: dict[str, Any]
) -> tuple[list[tuple[str, str, int]], list[tuple[str, str, int]]]:
    winners: list[tuple[str, str, int]] = []
    runners: list[tuple[str, str, int]] = []
    double_round = bool(rules["group_stage"].get("double_round_robin", True))

    for group_idx, group in enumerate(groups):
        stats = {team: {"pts": 0, "gd": 0, "gf": 0} for team in group}
        for team_a, team_b in combinations(group, 2):
            fixtures = [(team_a, team_b)]
            if double_round:
                fixtures.append((team_b, team_a))

            for home, away in fixtures:
                hg, ag = _sample_score(rng, ratings[home], ratings[away], neutral=False)
                stats[home]["gd"] += hg - ag
                stats[away]["gd"] += ag - hg
                stats[home]["gf"] += hg
                stats[away]["gf"] += ag

                if hg > ag:
                    stats[home]["pts"] += 3
                elif hg < ag:
                    stats[away]["pts"] += 3
                else:
                    stats[home]["pts"] += 1
                    stats[away]["pts"] += 1

        ranked = _rank_group(group, stats, ratings)
        winners.append((f"G{group_idx+1}", ranked[0], group_idx))
        runners.append((f"G{group_idx+1}", ranked[1], group_idx))

    return winners, runners


def _draw_round_of_16(
    rng: np.random.Generator, winners: list[tuple[str, str, int]], runners: list[tuple[str, str, int]]
) -> list[tuple[str, str]]:
    # winners/runners tuple format: (group_name, team_name, group_idx)
    for _ in range(200):
        free_runners = runners.copy()
        rng.shuffle(free_runners)
        pairs: list[tuple[str, str]] = []
        ok = True
        for winner_group, winner_team, winner_gid in winners:
            candidate_idx = None
            for i, (_r_group, _r_team, r_gid) in enumerate(free_runners):
                if r_gid != winner_gid:
                    candidate_idx = i
                    break
            if candidate_idx is None:
                ok = False
                break
            _group, runner_team, _gid = free_runners.pop(candidate_idx)
            pairs.append((winner_team, runner_team))
        if ok and len(pairs) == len(winners):
            return pairs

    # Fallback without group restriction.
    fallback = [(w[1], r[1]) for w, r in zip(winners, runners)]
    rng.shuffle(fallback)
    return fallback


def _pair_sequential(teams: list[str]) -> list[tuple[str, str]]:
    return [(teams[i], teams[i + 1]) for i in range(0, len(teams), 2)]


def simulate_tournament_once(
    rng: np.random.Generator,
    teams: list[str],
    ratings: dict[str, float],
    rules: dict[str, Any],
) -> str:
    shuffled = teams.copy()
    rng.shuffle(shuffled)

    group_count = int(rules["group_stage"].get("groups", 8))
    group_size = int(rules["group_stage"].get("group_size", 4))
    expected_teams = group_count * group_size
    if len(shuffled) != expected_teams:
        raise ValueError(f"Expected {expected_teams} teams, got {len(shuffled)}")

    groups = [shuffled[i : i + group_size] for i in range(0, len(shuffled), group_size)]
    winners, runners = _simulate_group_stage(rng, groups, ratings, rules)

    away_goals_rule = bool(rules["knockout"].get("away_goals_rule", True))

    r16_pairs = _draw_round_of_16(rng, winners, runners)
    r16_winners = [
        _play_two_legged_tie(rng, a, b, ratings, away_goals_rule=away_goals_rule)
        for a, b in r16_pairs
    ]

    rng.shuffle(r16_winners)
    qf_pairs = _pair_sequential(r16_winners)
    qf_two_legged = bool(rules["knockout"]["quarterfinals"].get("two_legged", True))
    qf_winners = [
        _play_two_legged_tie(rng, a, b, ratings, away_goals_rule=away_goals_rule)
        if qf_two_legged
        else _play_one_leg_tie(rng, a, b, ratings, neutral=True)
        for a, b in qf_pairs
    ]

    rng.shuffle(qf_winners)
    sf_pairs = _pair_sequential(qf_winners)
    sf_two_legged = bool(rules["knockout"]["semifinals"].get("two_legged", True))
    sf_winners = [
        _play_two_legged_tie(rng, a, b, ratings, away_goals_rule=away_goals_rule)
        if sf_two_legged
        else _play_one_leg_tie(rng, a, b, ratings, neutral=True)
        for a, b in sf_pairs
    ]

    final_two_legged = bool(rules["knockout"]["final"].get("two_legged", False))
    final_neutral = bool(rules["knockout"]["final"].get("neutral", True))
    if final_two_legged:
        champion = _play_two_legged_tie(
            rng, sf_winners[0], sf_winners[1], ratings, away_goals_rule=away_goals_rule
        )
    else:
        champion = _play_one_leg_tie(
            rng, sf_winners[0], sf_winners[1], ratings, neutral=final_neutral
        )
    return champion


def simulate_champion_probs(
    teams: list[str],
    ratings: dict[str, float],
    rules: dict[str, Any],
    n_simulations: int,
    random_seed: int = 42,
) -> dict[str, float]:
    rng = np.random.default_rng(random_seed)
    champion_counts = {team: 0 for team in teams}

    for _ in range(n_simulations):
        champion = simulate_tournament_once(rng, teams, ratings, rules)
        champion_counts[champion] += 1

    return {team: champion_counts[team] / float(n_simulations) for team in teams}
