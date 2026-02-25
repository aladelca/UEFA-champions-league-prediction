from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

import pandas as pd

from src.utils.io import read_dataframe, resolve_existing_data_path


FEATURES_PATH = Path("data/interim/feature_store_pre_match.parquet")
REPORT_PATH = Path("artifacts/reports/time_split_report.md")


@dataclass
class RollingSplit:
    train_seasons: list[int]
    valid_season: int
    train_idx: list[int]
    valid_idx: list[int]


def split_train_test_by_season(
    df: pd.DataFrame, test_season: int = 2021, season_col: str = "season"
) -> tuple[pd.DataFrame, pd.DataFrame]:
    train_valid_df = df[df[season_col] < test_season].copy()
    test_df = df[df[season_col] == test_season].copy()

    if train_valid_df.empty:
        raise ValueError("train_valid split is empty")
    if test_df.empty:
        raise ValueError("test split is empty")

    return train_valid_df, test_df


def rolling_origin_splits(
    df: pd.DataFrame, season_col: str = "season", min_train_seasons: int = 5
) -> List[RollingSplit]:
    seasons = sorted(int(s) for s in df[season_col].unique())
    if len(seasons) <= min_train_seasons:
        raise ValueError("Not enough seasons for rolling-origin with given min_train_seasons")

    splits: List[RollingSplit] = []
    for i in range(min_train_seasons, len(seasons)):
        train_seasons = seasons[:i]
        valid_season = seasons[i]

        train_idx = df[df[season_col].isin(train_seasons)].index.tolist()
        valid_idx = df[df[season_col] == valid_season].index.tolist()

        splits.append(
            RollingSplit(
                train_seasons=train_seasons,
                valid_season=valid_season,
                train_idx=train_idx,
                valid_idx=valid_idx,
            )
        )
    return splits


def write_split_report(
    train_valid_df: pd.DataFrame,
    test_df: pd.DataFrame,
    splits: list[RollingSplit],
    season_col: str = "season",
) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tv_seasons = sorted(train_valid_df[season_col].unique().tolist())
    test_season = int(test_df[season_col].iloc[0])

    lines = [
        "# Time Split Report",
        "",
        f"- train_valid_seasons: {tv_seasons}",
        f"- test_season: {test_season}",
        f"- rolling_splits: {len(splits)}",
        "",
        "| split | train_seasons | valid_season | train_rows | valid_rows |",
        "|---|---|---:|---:|---:|",
    ]

    for i, split in enumerate(splits, start=1):
        lines.append(
            f"| {i} | {split.train_seasons} | {split.valid_season} | {len(split.train_idx)} | {len(split.valid_idx)} |"
        )

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    if resolve_existing_data_path(FEATURES_PATH) is None:
        from src.features.build_pre_match_features import main as build_features_main

        build_features_main()

    df = read_dataframe(FEATURES_PATH, parse_dates=["Date"])
    df = df.sort_values(["Date", "match_id"]).reset_index(drop=True)

    train_valid_df, test_df = split_train_test_by_season(df, test_season=2021, season_col="season")
    splits = rolling_origin_splits(train_valid_df, season_col="season", min_train_seasons=5)
    write_split_report(train_valid_df, test_df, splits, season_col="season")

    print(f"saved={REPORT_PATH}")
    print(f"rolling_splits={len(splits)}")


if __name__ == "__main__":
    main()
