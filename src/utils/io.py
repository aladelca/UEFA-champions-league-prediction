from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd


def _csv_alternative(path: Path) -> Path:
    return path.with_suffix(".csv")


def write_dataframe(df: pd.DataFrame, preferred_path: Path, index: bool = False) -> Path:
    preferred_path.parent.mkdir(parents=True, exist_ok=True)
    if preferred_path.suffix == ".parquet":
        try:
            df.to_parquet(preferred_path, index=index)
            return preferred_path
        except Exception:
            csv_path = _csv_alternative(preferred_path)
            df.to_csv(csv_path, index=index)
            return csv_path

    if preferred_path.suffix == ".csv":
        df.to_csv(preferred_path, index=index)
        return preferred_path

    raise ValueError(f"Unsupported extension: {preferred_path.suffix}")


def resolve_existing_data_path(preferred_path: Path) -> Optional[Path]:
    if preferred_path.exists():
        return preferred_path
    if preferred_path.suffix == ".parquet":
        csv_path = _csv_alternative(preferred_path)
        if csv_path.exists():
            return csv_path
    return None


def read_dataframe(path: Path, parse_dates: Optional[list[str]] = None) -> pd.DataFrame:
    resolved = resolve_existing_data_path(path)
    if resolved is None:
        raise FileNotFoundError(f"File not found: {path}")

    if resolved.suffix == ".parquet":
        return pd.read_parquet(resolved)
    if resolved.suffix == ".csv":
        return pd.read_csv(resolved, parse_dates=parse_dates)
    raise ValueError(f"Unsupported extension: {resolved.suffix}")
