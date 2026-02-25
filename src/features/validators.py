from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

from src.utils.io import read_dataframe, resolve_existing_data_path


FEATURES_PATH = Path("data/interim/feature_store_pre_match.parquet")
REPORT_PATH = Path("artifacts/reports/leakage_gates_report.md")

BLOCKED_COLUMNS = {
    "score",
    "score_opp",
    "result",
    "home_goals",
    "away_goals",
}

REQUIRED_COLUMNS = {
    "match_id",
    "season",
    "Date",
    "home_team",
    "away_team",
    "y_match",
    "home_flag",
    "elo_home",
    "elo_away",
    "elo_diff",
    "season_home_matches_before",
    "season_away_matches_before",
    "guardrail_same_day_batch_mode",
}


@dataclass
class LeakageCheckResult:
    name: str
    passed: bool
    message: str


def validate_no_blocked_columns(columns: Iterable[str]) -> LeakageCheckResult:
    cols = set(columns)
    blocked = sorted(cols.intersection(BLOCKED_COLUMNS))
    if blocked:
        return LeakageCheckResult(
            name="no_blocked_columns",
            passed=False,
            message=f"blocked_columns_present={blocked}",
        )
    return LeakageCheckResult(name="no_blocked_columns", passed=True, message="ok")


def validate_required_columns(columns: Iterable[str]) -> LeakageCheckResult:
    cols = set(columns)
    missing = sorted(REQUIRED_COLUMNS - cols)
    if missing:
        return LeakageCheckResult(
            name="required_columns",
            passed=False,
            message=f"missing_columns={missing}",
        )
    return LeakageCheckResult(name="required_columns", passed=True, message="ok")


def validate_temporal_sort(df: pd.DataFrame) -> LeakageCheckResult:
    expected = df.sort_values(["Date", "match_id"]).index.tolist()
    current = df.index.tolist()
    if expected != current:
        return LeakageCheckResult(
            name="temporal_sort",
            passed=False,
            message="rows_not_sorted_by_date_match_id",
        )
    return LeakageCheckResult(name="temporal_sort", passed=True, message="ok")


def validate_non_negative_counters(df: pd.DataFrame) -> LeakageCheckResult:
    check_cols = [
        "season_home_matches_before",
        "season_away_matches_before",
        "global_home_matches_before",
        "global_away_matches_before",
    ]
    existing = [c for c in check_cols if c in df.columns]
    negatives = {}
    for col in existing:
        count = int((df[col] < 0).sum())
        if count > 0:
            negatives[col] = count
    if negatives:
        return LeakageCheckResult(
            name="non_negative_counters",
            passed=False,
            message=f"negative_counts={negatives}",
        )
    return LeakageCheckResult(name="non_negative_counters", passed=True, message="ok")


def validate_team_match_counters(df: pd.DataFrame) -> LeakageCheckResult:
    home = df[["season", "Date", "match_id", "home_team", "season_home_matches_before"]].copy()
    home = home.rename(
        columns={
            "home_team": "team",
            "season_home_matches_before": "matches_before",
        }
    )

    away = df[["season", "Date", "match_id", "away_team", "season_away_matches_before"]].copy()
    away = away.rename(
        columns={
            "away_team": "team",
            "season_away_matches_before": "matches_before",
        }
    )

    long_df = pd.concat([home, away], ignore_index=True)
    long_df = long_df.sort_values(["season", "team", "Date", "match_id"]).reset_index(drop=True)

    failures: list[str] = []
    for (season, team), grp in long_df.groupby(["season", "team"], sort=False):
        observed = grp["matches_before"].astype(int).tolist()
        expected = list(range(len(observed)))
        if observed != expected:
            failures.append(f"{season}:{team}")
            if len(failures) >= 10:
                break

    if failures:
        return LeakageCheckResult(
            name="team_match_counters",
            passed=False,
            message=f"counter_sequence_mismatch={failures}",
        )
    return LeakageCheckResult(name="team_match_counters", passed=True, message="ok")


def validate_same_day_guardrail_flag(df: pd.DataFrame) -> LeakageCheckResult:
    if "guardrail_same_day_batch_mode" not in df.columns:
        return LeakageCheckResult(
            name="same_day_guardrail_flag",
            passed=False,
            message="guardrail_same_day_batch_mode_missing",
        )
    invalid = int((df["guardrail_same_day_batch_mode"] != 1).sum())
    if invalid > 0:
        return LeakageCheckResult(
            name="same_day_guardrail_flag",
            passed=False,
            message=f"invalid_rows={invalid}",
        )
    return LeakageCheckResult(name="same_day_guardrail_flag", passed=True, message="ok")


def run_all_leakage_checks(df: pd.DataFrame) -> list[LeakageCheckResult]:
    checks = [
        validate_no_blocked_columns(df.columns),
        validate_required_columns(df.columns),
        validate_temporal_sort(df),
        validate_non_negative_counters(df),
        validate_team_match_counters(df),
        validate_same_day_guardrail_flag(df),
    ]
    return checks


def write_leakage_report(results: list[LeakageCheckResult]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    passed_all = all(r.passed for r in results)

    lines = [
        "# Leakage Gates Report",
        "",
        f"- overall_status: {'PASS' if passed_all else 'FAIL'}",
        "",
        "| check | status | message |",
        "|---|---|---|",
    ]
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        lines.append(f"| `{result.name}` | {status} | {result.message} |")

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    if resolve_existing_data_path(FEATURES_PATH) is None:
        from src.features.build_pre_match_features import main as build_features_main

        build_features_main()

    df = read_dataframe(FEATURES_PATH, parse_dates=["Date"])
    df = df.sort_values(["Date", "match_id"]).reset_index(drop=True)
    results = run_all_leakage_checks(df)
    write_leakage_report(results)

    for result in results:
        print(f"{result.name}: {'PASS' if result.passed else 'FAIL'} - {result.message}")

    if not all(r.passed for r in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
