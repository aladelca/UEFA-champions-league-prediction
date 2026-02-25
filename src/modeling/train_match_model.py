from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.features.validators import validate_no_blocked_columns
from src.modeling.split_time import rolling_origin_splits, split_train_test_by_season
from src.utils.io import read_dataframe, resolve_existing_data_path


INTERIM_DIR = Path("data/interim")
MODEL_DIR = Path("artifacts/models")
REPORT_DIR = Path("artifacts/reports")
FEATURES_PATH = INTERIM_DIR / "feature_store_pre_match.parquet"
MODEL_PATH = MODEL_DIR / "match_model.joblib"
REPORT_PATH = REPORT_DIR / "evaluation_report.md"

CLASS_LABELS = [-1, 0, 1]
META_COLUMNS = {
    "match_id",
    "season",
    "Date",
    "home_team",
    "away_team",
    "y_match",
}


@dataclass
class CandidateResult:
    name: str
    fold_log_losses: list[float]
    mean_log_loss: float
    std_log_loss: float
    error: str | None = None


def _build_candidate_models() -> dict[str, Any]:
    models: dict[str, Any] = {
        "logistic_regression": Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                (
                    "model",
                    LogisticRegression(
                        max_iter=5000,
                        solver="lbfgs",
                        random_state=42,
                    ),
                ),
            ]
        ),
        "hist_gradient_boosting": HistGradientBoostingClassifier(
            random_state=42,
            max_depth=6,
        ),
        "random_forest": RandomForestClassifier(
            random_state=42,
            n_jobs=-1,
            n_estimators=300,
            max_depth=10,
            min_samples_leaf=2,
        ),
    }

    try:
        from catboost import CatBoostClassifier

        models["catboost"] = CatBoostClassifier(
            loss_function="MultiClass",
            random_seed=42,
            verbose=0,
        )
    except Exception:
        # CatBoost candidate is preferred but optional at runtime.
        pass

    return models


def _get_feature_columns(df: pd.DataFrame) -> list[str]:
    numeric_cols = [
        col
        for col in df.columns
        if col not in META_COLUMNS and pd.api.types.is_numeric_dtype(df[col])
    ]
    variable_cols = [col for col in numeric_cols if df[col].nunique(dropna=False) > 1]
    return sorted(variable_cols)


def _aligned_proba(model: Any, X: pd.DataFrame, labels: list[int]) -> np.ndarray:
    proba = model.predict_proba(X)
    model_classes = list(getattr(model, "classes_", labels))
    if model_classes == labels:
        return proba

    order = [model_classes.index(label) for label in labels]
    return proba[:, order]


def _evaluate_candidate(
    name: str,
    model: Any,
    X: pd.DataFrame,
    y: pd.Series,
    splits: list,
) -> CandidateResult:
    fold_losses: list[float] = []

    for split in splits:
        X_train = X.iloc[split.train_idx]
        y_train = y.iloc[split.train_idx]
        X_valid = X.iloc[split.valid_idx]
        y_valid = y.iloc[split.valid_idx]

        model.fit(X_train, y_train)
        proba = _aligned_proba(model, X_valid, labels=CLASS_LABELS)
        loss = log_loss(y_valid, proba, labels=CLASS_LABELS)
        fold_losses.append(float(loss))

    return CandidateResult(
        name=name,
        fold_log_losses=fold_losses,
        mean_log_loss=float(np.mean(fold_losses)),
        std_log_loss=float(np.std(fold_losses)),
    )


def write_evaluation_report(
    feature_cols: list[str],
    candidate_results: list[CandidateResult],
    best_name: str,
    test_log_loss_value: float,
) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Evaluation Report",
        "",
        "- objective: multiclass match outcome",
        "- primary_metric: log_loss",
        f"- selected_model: {best_name}",
        f"- test_log_loss: {test_log_loss_value:.6f}",
        f"- n_features: {len(feature_cols)}",
        "",
        "| model | cv_mean_log_loss | cv_std_log_loss | folds | status |",
        "|---|---:|---:|---:|---|",
    ]

    for result in candidate_results:
        if result.error:
            lines.append(f"| {result.name} | - | - | - | ERROR: {result.error} |")
        else:
            lines.append(
                f"| {result.name} | {result.mean_log_loss:.6f} | {result.std_log_loss:.6f} | {len(result.fold_log_losses)} | OK |"
            )

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    if resolve_existing_data_path(FEATURES_PATH) is None:
        from src.features.build_pre_match_features import main as build_features_main

        build_features_main()

    df = read_dataframe(FEATURES_PATH, parse_dates=["Date"])
    df = df.sort_values(["Date", "match_id"]).reset_index(drop=True)

    leakage = validate_no_blocked_columns(df.columns)
    if not leakage.passed:
        raise ValueError(leakage.message)

    train_valid_df, test_df = split_train_test_by_season(df, test_season=2021, season_col="season")
    train_valid_df = train_valid_df.sort_values(["Date", "match_id"]).reset_index(drop=True)
    test_df = test_df.sort_values(["Date", "match_id"]).reset_index(drop=True)
    splits = rolling_origin_splits(train_valid_df, season_col="season", min_train_seasons=5)

    feature_cols = _get_feature_columns(train_valid_df)
    X_tv = train_valid_df[feature_cols]
    y_tv = train_valid_df["y_match"].astype(int)
    X_test = test_df[feature_cols]
    y_test = test_df["y_match"].astype(int)

    candidate_results: list[CandidateResult] = []
    candidate_models = _build_candidate_models()

    for name, model in candidate_models.items():
        try:
            result = _evaluate_candidate(name, model, X_tv, y_tv, splits)
        except Exception as exc:
            result = CandidateResult(
                name=name,
                fold_log_losses=[],
                mean_log_loss=float("inf"),
                std_log_loss=float("inf"),
                error=str(exc),
            )
        candidate_results.append(result)

    successful = [r for r in candidate_results if r.error is None]
    if not successful:
        raise RuntimeError("No model candidate finished successfully.")

    successful.sort(key=lambda r: r.mean_log_loss)
    best_name = successful[0].name
    best_model = _build_candidate_models()[best_name]

    best_model.fit(X_tv, y_tv)
    test_proba = _aligned_proba(best_model, X_test, labels=CLASS_LABELS)
    test_log_loss_value = float(log_loss(y_test, test_proba, labels=CLASS_LABELS))

    model_payload = {
        "model_name": best_name,
        "model": best_model,
        "feature_columns": feature_cols,
        "class_labels": CLASS_LABELS,
        "cv_results": [
            {
                "model": r.name,
                "mean_log_loss": r.mean_log_loss,
                "std_log_loss": r.std_log_loss,
                "fold_log_losses": r.fold_log_losses,
                "error": r.error,
            }
            for r in candidate_results
        ],
        "test_log_loss": test_log_loss_value,
    }

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model_payload, MODEL_PATH)
    write_evaluation_report(feature_cols, candidate_results, best_name, test_log_loss_value)

    print(f"saved={MODEL_PATH}")
    print(f"selected_model={best_name}")
    print(f"test_log_loss={test_log_loss_value:.6f}")


if __name__ == "__main__":
    main()
