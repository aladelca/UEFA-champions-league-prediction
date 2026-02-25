#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.inference.predict_champion import simulate_season_from_start


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate preseason champion probabilities for one season.")
    parser.add_argument("--season", type=int, required=True, help="Season key in dataset (e.g., 2021)")
    parser.add_argument("--n-simulations", type=int, default=10000)
    parser.add_argument("--random-seed", type=int, default=42)
    parser.add_argument(
        "--output",
        type=str,
        default="artifacts/reports/predictions_latest.csv",
        help="CSV output path",
    )
    args = parser.parse_args()

    result = simulate_season_from_start(
        season=args.season,
        n_simulations=args.n_simulations,
        random_seed=args.random_seed,
    )
    df = pd.DataFrame(result["results"])
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"saved={out_path}")
    print(df.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
