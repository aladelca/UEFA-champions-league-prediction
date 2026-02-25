import pandas as pd

from src.features.build_pre_match_features import build_feature_store
from src.features.validators import run_all_leakage_checks, validate_no_blocked_columns


def _sample_features() -> pd.DataFrame:
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
            "Date": "2021-09-21",
            "home_team": "A",
            "away_team": "C",
            "home_goals": 1,
            "away_goals": 1,
            "y_match": 0,
        },
        {
            "match_id": "m3",
            "season": 2021,
            "Date": "2021-09-28",
            "home_team": "B",
            "away_team": "C",
            "home_goals": 0,
            "away_goals": 2,
            "y_match": -1,
        },
    ]
    matches = pd.DataFrame(rows)
    matches["Date"] = pd.to_datetime(matches["Date"])
    return build_feature_store(matches).sort_values(["Date", "match_id"]).reset_index(drop=True)


def test_all_leakage_checks_pass_for_valid_feature_store() -> None:
    features = _sample_features()
    results = run_all_leakage_checks(features)
    assert all(r.passed for r in results)


def test_blocked_column_is_detected() -> None:
    features = _sample_features()
    features["score"] = 1
    result = validate_no_blocked_columns(features.columns)
    assert result.passed is False
