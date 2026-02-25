from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


RULES_DIR = Path("configs/tournament_rules")


def default_rules_for_season(season: int) -> dict[str, Any]:
    quarterfinal_one_leg = season == 2019
    semifinal_one_leg = season == 2019
    away_goals_rule = season <= 2020

    return {
        "season": season,
        "format": "ucl_32_teams",
        "group_stage": {
            "groups": 8,
            "group_size": 4,
            "double_round_robin": True,
        },
        "knockout": {
            "round_of_16": {"two_legged": True},
            "quarterfinals": {"two_legged": not quarterfinal_one_leg},
            "semifinals": {"two_legged": not semifinal_one_leg},
            "final": {"two_legged": False, "neutral": True},
            "away_goals_rule": away_goals_rule,
        },
        "exceptions": {
            "quarterfinal_one_leg": quarterfinal_one_leg,
            "semifinal_one_leg": semifinal_one_leg,
            "away_goals_removed": not away_goals_rule,
        },
    }


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for key, value in override.items():
        if key in out and isinstance(out[key], dict) and isinstance(value, dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def load_rules_for_season(season: int) -> dict[str, Any]:
    defaults = default_rules_for_season(season)
    path = RULES_DIR / f"ucl_{season}.yaml"
    if not path.exists():
        return defaults

    with path.open("r", encoding="utf-8") as f:
        user_rules = yaml.safe_load(f) or {}
    return _deep_merge(defaults, user_rules)
