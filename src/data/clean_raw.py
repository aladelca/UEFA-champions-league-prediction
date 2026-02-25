from pathlib import Path

import pandas as pd

from src.data.load_raw import load_raw_df
from src.utils.io import write_dataframe


INTERIM_DIR = Path("data/interim")
REPORT_DIR = Path("artifacts/reports")
OUTPUT_PATH = INTERIM_DIR / "matches_raw_clean.parquet"
REPORT_PATH = REPORT_DIR / "profiling_report.md"


def _fix_mojibake(value: object) -> object:
    if not isinstance(value, str):
        return value
    if "Ã" not in value and "Â" not in value:
        return value
    try:
        return value.encode("latin1").decode("utf-8")
    except Exception:
        return value


def clean_raw_df(df: pd.DataFrame) -> pd.DataFrame:
    clean = df.copy()

    unnamed_cols = [c for c in clean.columns if c.lower().startswith("unnamed")]
    if unnamed_cols:
        clean = clean.drop(columns=unnamed_cols)

    if "Date" in clean.columns:
        clean["Date"] = pd.to_datetime(clean["Date"], errors="coerce")

    for col in ["team", "team_opp"]:
        if col in clean.columns:
            clean[col] = clean[col].map(_fix_mojibake)

    return clean


def write_profile_report(raw_df: pd.DataFrame, clean_df: pd.DataFrame) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    null_count = int(clean_df.isna().sum().sum())
    duplicated_rows = int(clean_df.duplicated().sum())
    seasons = (
        f"{int(clean_df['season'].min())}-{int(clean_df['season'].max())}"
        if "season" in clean_df.columns
        else "n/a"
    )
    with REPORT_PATH.open("w", encoding="utf-8") as f:
        f.write("# Profiling Report (Initial)\n\n")
        f.write(f"- raw_shape: {raw_df.shape}\n")
        f.write(f"- clean_shape: {clean_df.shape}\n")
        f.write(f"- null_values_total: {null_count}\n")
        f.write(f"- duplicated_rows: {duplicated_rows}\n")
        f.write(f"- seasons: {seasons}\n")


def main() -> None:
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    raw_df = load_raw_df()
    clean_df = clean_raw_df(raw_df)
    saved_path = write_dataframe(clean_df, OUTPUT_PATH, index=False)
    write_profile_report(raw_df, clean_df)
    print(f"saved={saved_path}")
    print(f"rows={len(clean_df)}")


if __name__ == "__main__":
    main()
