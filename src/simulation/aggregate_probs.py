from pathlib import Path

import pandas as pd

from src.inference.predict_champion import simulate_season_from_start
from src.utils.io import write_dataframe


OUT_PATH = Path("data/processed/team_season_probs.parquet")


def main() -> None:
    rows = []
    for season in range(2010, 2022):
        payload = simulate_season_from_start(season=season, n_simulations=5000, random_seed=42)
        for item in payload["results"]:
            rows.append(
                {
                    "season": season,
                    "team": item["team"],
                    "p_champion": item["p_champion"],
                    "rank": item["rank"],
                }
            )
    out_df = pd.DataFrame(rows)
    saved_path = write_dataframe(out_df, OUT_PATH, index=False)
    print(f"saved={saved_path}")


if __name__ == "__main__":
    main()
