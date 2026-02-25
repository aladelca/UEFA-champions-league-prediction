from pathlib import Path

import numpy as np
import pandas as pd

from src.utils.io import read_dataframe, write_dataframe


INTERIM_DIR = Path("data/interim")
CLEAN_PATH = INTERIM_DIR / "matches_raw_clean.parquet"
OUT_PATH = INTERIM_DIR / "matches_unique.parquet"


def _load_clean_df() -> pd.DataFrame:
    from src.utils.io import resolve_existing_data_path

    if resolve_existing_data_path(CLEAN_PATH) is None:
        from src.data.clean_raw import main as clean_main

        clean_main()
    return read_dataframe(CLEAN_PATH, parse_dates=["Date"])


def _create_match_id(df: pd.DataFrame) -> pd.Series:
    return (
        df["season"].astype(str)
        + "_"
        + df["Date"].dt.strftime("%Y-%m-%d")
        + "_"
        + df["team"].astype(str)
        + "_vs_"
        + df["team_opp"].astype(str)
    )


def build_matches_unique(df: pd.DataFrame) -> pd.DataFrame:
    required = {"season", "Date", "team", "team_opp", "home", "score", "score_opp"}
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    work = df.copy()
    work["Date"] = pd.to_datetime(work["Date"], errors="coerce")
    home_rows = work[work["home"] == 1].copy()

    home_rows["match_id"] = _create_match_id(home_rows)
    home_rows["home_team"] = home_rows["team"]
    home_rows["away_team"] = home_rows["team_opp"]
    home_rows["home_goals"] = home_rows["score"]
    home_rows["away_goals"] = home_rows["score_opp"]

    home_rows["y_match"] = np.select(
        [
            home_rows["home_goals"] > home_rows["away_goals"],
            home_rows["home_goals"] == home_rows["away_goals"],
        ],
        [1, 0],
        default=-1,
    )

    out_cols = [
        "match_id",
        "season",
        "Date",
        "home_team",
        "away_team",
        "home_goals",
        "away_goals",
        "y_match",
    ]
    matches = home_rows[out_cols].sort_values(["season", "Date", "match_id"]).reset_index(drop=True)

    if matches["match_id"].duplicated().any():
        dup_count = int(matches["match_id"].duplicated().sum())
        raise ValueError(f"Duplicated match_id detected: {dup_count}")

    return matches


def main() -> None:
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    clean_df = _load_clean_df()
    matches = build_matches_unique(clean_df)
    saved_path = write_dataframe(matches, OUT_PATH, index=False)
    print(f"saved={saved_path}")
    print(f"rows={len(matches)}")


if __name__ == "__main__":
    main()
