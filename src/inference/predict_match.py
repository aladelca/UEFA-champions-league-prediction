from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd


MODEL_PATH = Path("artifacts/models/match_model.joblib")
_MODEL_PAYLOAD: dict[str, Any] | None = None


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def _predict_with_heuristic(home_flag: int, features: dict[str, float]) -> dict[str, float]:
    elo_diff = float(features.get("elo_diff", 0.0))
    x = (elo_diff / 200.0) + (0.12 if home_flag == 1 else 0.0)
    p_home_vs_away = _sigmoid(x)

    p_draw = max(0.15, 0.30 - min(abs(x) * 0.08, 0.12))
    mass = 1.0 - p_draw
    p_home = mass * p_home_vs_away
    p_away = mass * (1.0 - p_home_vs_away)

    total = p_home + p_draw + p_away
    return {
        "p_home_win": round(float(p_home / total), 6),
        "p_draw": round(float(p_draw / total), 6),
        "p_away_win": round(float(p_away / total), 6),
    }


def _load_model_payload() -> dict[str, Any] | None:
    global _MODEL_PAYLOAD
    if _MODEL_PAYLOAD is not None:
        return _MODEL_PAYLOAD
    if not MODEL_PATH.exists():
        return None

    payload = joblib.load(MODEL_PATH)
    if not isinstance(payload, dict) or "model" not in payload:
        return None
    _MODEL_PAYLOAD = payload
    return payload


def _prepare_row(features: dict[str, float], feature_columns: list[str], home_flag: int) -> pd.DataFrame:
    row = {col: 0.0 for col in feature_columns}
    for key, value in features.items():
        if key in row:
            row[key] = float(value)
    if "home_flag" in row:
        row["home_flag"] = float(home_flag)
    if "elo_diff_abs" in row and "elo_diff" in row:
        row["elo_diff_abs"] = abs(row["elo_diff"])
    if "elo_diff_sq" in row and "elo_diff" in row:
        row["elo_diff_sq"] = row["elo_diff"] ** 2
    return pd.DataFrame([row], columns=feature_columns)


def _align_proba(model: Any, X: pd.DataFrame, labels: list[int]) -> np.ndarray:
    proba = model.predict_proba(X)
    classes = [int(c) for c in getattr(model, "classes_", labels)]
    if classes == labels:
        return proba
    order = [classes.index(c) for c in labels]
    return proba[:, order]


def predict_match_probabilities(home_flag: int, features: dict[str, float]) -> dict[str, float]:
    payload = _load_model_payload()
    if payload is None:
        return _predict_with_heuristic(home_flag=home_flag, features=features)

    model = payload["model"]
    class_labels = [int(c) for c in payload.get("class_labels", [-1, 0, 1])]
    feature_columns = payload.get("feature_columns", [])
    if not feature_columns:
        return _predict_with_heuristic(home_flag=home_flag, features=features)

    X = _prepare_row(features=features, feature_columns=feature_columns, home_flag=home_flag)
    proba = _align_proba(model, X, labels=class_labels)[0]
    idx = {label: i for i, label in enumerate(class_labels)}

    return {
        "p_home_win": round(float(proba[idx[1]]), 6),
        "p_draw": round(float(proba[idx[0]]), 6),
        "p_away_win": round(float(proba[idx[-1]]), 6),
    }
