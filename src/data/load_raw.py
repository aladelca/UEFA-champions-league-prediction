from pathlib import Path

import pandas as pd


RAW_CANDIDATES = [
    Path("data/raw/df.csv"),
    Path("data/df.csv"),
]


def get_raw_path() -> Path:
    for candidate in RAW_CANDIDATES:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("Raw CSV not found in data/raw/df.csv or data/df.csv")


def load_raw_df() -> pd.DataFrame:
    return pd.read_csv(get_raw_path())


if __name__ == "__main__":
    df = load_raw_df()
    print(f"loaded_raw_shape={df.shape}")
