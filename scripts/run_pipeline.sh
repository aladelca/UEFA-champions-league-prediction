#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"
if [[ -x ".venv/bin/python" ]]; then
  PYTHON_BIN=".venv/bin/python"
fi

echo "[1/8] clean raw"
"$PYTHON_BIN" -m src.data.clean_raw

echo "[2/8] build unique matches"
"$PYTHON_BIN" -m src.data.build_matches_unique

echo "[3/8] build features"
"$PYTHON_BIN" -m src.features.build_pre_match_features

echo "[4/8] leakage gates"
"$PYTHON_BIN" -m src.features.validators

echo "[5/8] build time splits"
"$PYTHON_BIN" -m src.modeling.split_time

echo "[6/8] run experiments and select principal model"
"$PYTHON_BIN" -m src.modeling.run_experiments

echo "[7/8] evaluate principal model/reporting"
"$PYTHON_BIN" -m src.modeling.evaluate

echo "[8/8] simulate champion probabilities"
"$PYTHON_BIN" -m src.simulation.aggregate_probs

echo "pipeline completed"
