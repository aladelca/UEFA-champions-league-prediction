import pandas as pd

from src.features.build_pre_match_features import build_feature_store
from src.features.validators import validate_no_blocked_columns


def _sample_matches() -> pd.DataFrame:
    rows = [
        {
            "match_id": "m1",
            "season": 2021,
            "Date": "2021-09-14",
            "home_team": "A",
            "away_team": "B",
            "home_goals": 1,
            "away_goals": 0,
            "y_match": 1,
        },
        {
            "match_id": "m2",
            "season": 2021,
            "Date": "2021-09-14",
            "home_team": "C",
            "away_team": "D",
            "home_goals": 0,
            "away_goals": 0,
            "y_match": 0,
        },
        {
            "match_id": "m3",
            "season": 2021,
            "Date": "2021-09-21",
            "home_team": "A",
            "away_team": "C",
            "home_goals": 2,
            "away_goals": 1,
            "y_match": 1,
        },
    ]
    df = pd.DataFrame(rows)
    df["Date"] = pd.to_datetime(df["Date"])
    return df


def test_feature_builder_uses_t_minus_1_logic() -> None:
    matches = _sample_matches()
    features = build_feature_store(matches)

    first = features[features["match_id"] == "m1"].iloc[0]
    second = features[features["match_id"] == "m2"].iloc[0]
    third = features[features["match_id"] == "m3"].iloc[0]

    assert int(first["season_home_matches_before"]) == 0
    assert int(first["season_away_matches_before"]) == 0
    assert int(second["season_home_matches_before"]) == 0
    assert int(second["season_away_matches_before"]) == 0

    assert int(third["season_home_matches_before"]) == 1
    assert int(third["season_away_matches_before"]) == 1
    assert float(third["form_points_home_last5"]) == 3.0
    assert float(third["form_points_away_last5"]) == 1.0
    assert int(third["guardrail_same_day_batch_mode"]) == 1


def test_feature_builder_excludes_blocked_columns() -> None:
    matches = _sample_matches()
    features = build_feature_store(matches)
    res = validate_no_blocked_columns(features.columns)
    assert res.passed is True
