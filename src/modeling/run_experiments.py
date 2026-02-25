from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import yaml
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, log_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.features.validators import validate_no_blocked_columns
from src.modeling.split_time import rolling_origin_splits, split_train_test_by_season
from src.utils.io import read_dataframe, resolve_existing_data_path


FEATURES_PATH = Path("data/interim/feature_store_pre_match.parquet")
MODEL_PATH = Path("artifacts/models/match_model.joblib")
REPORT_PATH = Path("artifacts/reports/experiments_comparison.md")
MODEL_CONFIG_PATH = Path("configs/model.yaml")

CLASS_LABELS = [-1, 0, 1]
META_COLUMNS = {"match_id", "season", "Date", "home_team", "away_team", "y_match"}


@dataclass
class Experiment:
    exp_id: str
    feature_variant: str
    model_name: str
    params: dict[str, Any]


def _multiclass_brier(y_true: np.ndarray, proba: np.ndarray, labels: list[int]) -> float:
    label_to_idx = {label: i for i, label in enumerate(labels)}
    one_hot = np.zeros((len(y_true), len(labels)), dtype=float)
    for row_i, y in enumerate(y_true):
        one_hot[row_i, label_to_idx[int(y)]] = 1.0
    return float(np.mean(np.sum((proba - one_hot) ** 2, axis=1)))


def _align_proba(model: Any, X: pd.DataFrame) -> np.ndarray:
    proba = model.predict_proba(X)
    classes = [int(c) for c in getattr(model, "classes_", CLASS_LABELS)]
    if classes == CLASS_LABELS:
        return proba
    order = [classes.index(c) for c in CLASS_LABELS]
    return proba[:, order]


def _predict_labels_from_proba(proba: np.ndarray) -> np.ndarray:
    idx = np.argmax(proba, axis=1)
    return np.array([CLASS_LABELS[i] for i in idx], dtype=int)


def _build_model(model_name: str, params: dict[str, Any]) -> Any:
    if model_name == "logistic_regression":
        return Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                (
                    "model",
                    LogisticRegression(
                        max_iter=8000,
                        solver="lbfgs",
                        random_state=42,
                        **params,
                    ),
                ),
            ]
        )

    if model_name == "hist_gradient_boosting":
        return HistGradientBoostingClassifier(random_state=42, **params)

    if model_name == "random_forest":
        return RandomForestClassifier(random_state=42, n_jobs=-1, **params)

    if model_name == "catboost":
        from catboost import CatBoostClassifier

        return CatBoostClassifier(
            loss_function="MultiClass",
            random_seed=42,
            verbose=0,
            **params,
        )

    raise ValueError(f"Unsupported model_name={model_name}")


def _prepare_feature_variants(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    base = df.copy()
    numeric_cols = [c for c in base.columns if c not in META_COLUMNS and pd.api.types.is_numeric_dtype(base[c])]
    numeric_cols = [c for c in numeric_cols if base[c].nunique(dropna=False) > 1]

    core_cols = [
        "home_flag",
        "elo_home",
        "elo_away",
        "elo_diff",
        "form_points_home_last5",
        "form_points_away_last5",
        "goal_diff_home_last5",
        "goal_diff_away_last5",
    ]
    core_cols = [c for c in core_cols if c in numeric_cols]
    core = base[core_cols].copy()

    extended = base[numeric_cols].copy()

    extended_fe = extended.copy()

    def _safe_ratio(num: pd.Series, den: pd.Series, default: float = 1.0) -> pd.Series:
        ratio = num / den.replace(0.0, np.nan)
        ratio = ratio.replace([np.inf, -np.inf], np.nan)
        return ratio.fillna(default)
    if "elo_diff" in extended_fe.columns:
        extended_fe["elo_diff_abs"] = extended_fe["elo_diff"].abs()
        extended_fe["elo_diff_sq"] = extended_fe["elo_diff"] ** 2

    if {"form_points_home_last5", "form_points_away_last5"} <= set(extended_fe.columns):
        extended_fe["form_points_ratio_last5"] = _safe_ratio(
            extended_fe["form_points_home_last5"] + 1.0,
            extended_fe["form_points_away_last5"] + 1.0,
            default=1.0,
        )
        extended_fe["form_points_sum_last5"] = (
            extended_fe["form_points_home_last5"] + extended_fe["form_points_away_last5"]
        )

    if {"goal_diff_home_last5", "goal_diff_away_last5"} <= set(extended_fe.columns):
        extended_fe["form_goal_diff_ratio_last5"] = _safe_ratio(
            extended_fe["goal_diff_home_last5"] + 10.0,
            extended_fe["goal_diff_away_last5"] + 10.0,
            default=1.0,
        )
        extended_fe["form_goal_diff_sum_last5"] = (
            extended_fe["goal_diff_home_last5"] + extended_fe["goal_diff_away_last5"]
        )

    if {"season_home_ppg_before", "season_away_ppg_before"} <= set(extended_fe.columns):
        extended_fe["season_ppg_ratio_before"] = _safe_ratio(
            extended_fe["season_home_ppg_before"] + 0.05,
            extended_fe["season_away_ppg_before"] + 0.05,
            default=1.0,
        )
        extended_fe["season_ppg_sum_before"] = (
            extended_fe["season_home_ppg_before"] + extended_fe["season_away_ppg_before"]
        )

    if {"global_home_ppg_before", "global_away_ppg_before"} <= set(extended_fe.columns):
        extended_fe["global_ppg_ratio_before"] = _safe_ratio(
            extended_fe["global_home_ppg_before"] + 0.05,
            extended_fe["global_away_ppg_before"] + 0.05,
            default=1.0,
        )
        extended_fe["global_ppg_sum_before"] = (
            extended_fe["global_home_ppg_before"] + extended_fe["global_away_ppg_before"]
        )

    if {"season_home_matches_before", "season_away_matches_before"} <= set(extended_fe.columns):
        extended_fe["season_experience_diff"] = (
            extended_fe["season_home_matches_before"] - extended_fe["season_away_matches_before"]
        )

    if {"global_home_matches_before", "global_away_matches_before"} <= set(extended_fe.columns):
        extended_fe["global_experience_diff"] = (
            extended_fe["global_home_matches_before"] - extended_fe["global_away_matches_before"]
        )

    # Safety guard for downstream models.
    extended = extended.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    extended_fe = extended_fe.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    core = core.replace([np.inf, -np.inf], np.nan).fillna(0.0)

    return {
        "core": core,
        "extended": extended,
        "extended_fe": extended_fe,
    }


def _build_experiments() -> list[Experiment]:
    model_grid: dict[str, list[dict[str, Any]]] = {
        "logistic_regression": [
            {"C": 0.6},
            {"C": 2.0},
        ],
        "hist_gradient_boosting": [
            {"learning_rate": 0.05, "max_depth": 4, "max_iter": 350},
            {"learning_rate": 0.08, "max_depth": 8, "max_iter": 500},
        ],
        "random_forest": [
            {"n_estimators": 250, "max_depth": 10, "min_samples_leaf": 2},
            {"n_estimators": 400, "max_depth": None, "min_samples_leaf": 1},
        ],
        "catboost": [
            {"depth": 6, "learning_rate": 0.05, "iterations": 500, "l2_leaf_reg": 5.0},
            {"depth": 8, "learning_rate": 0.03, "iterations": 800, "l2_leaf_reg": 3.0},
        ],
    }
    variants = ["core", "extended", "extended_fe"]

    experiments: list[Experiment] = []
    exp_num = 1
    for variant in variants:
        for model_name, params_list in model_grid.items():
            for params in params_list:
                experiments.append(
                    Experiment(
                        exp_id=f"EXP-{exp_num:03d}",
                        feature_variant=variant,
                        model_name=model_name,
                        params=params,
                    )
                )
                exp_num += 1
    return experiments


def _evaluate_experiment(
    exp: Experiment,
    X_tv: pd.DataFrame,
    y_tv: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    splits: list,
) -> dict[str, Any]:
    fold_log_loss: list[float] = []
    fold_brier: list[float] = []
    fold_macro_f1: list[float] = []

    for split in splits:
        model = _build_model(exp.model_name, exp.params)
        X_train = X_tv.iloc[split.train_idx]
        y_train = y_tv.iloc[split.train_idx]
        X_valid = X_tv.iloc[split.valid_idx]
        y_valid = y_tv.iloc[split.valid_idx]

        model.fit(X_train, y_train)
        proba = _align_proba(model, X_valid)
        pred = _predict_labels_from_proba(proba)

        fold_log_loss.append(float(log_loss(y_valid, proba, labels=CLASS_LABELS)))
        fold_brier.append(_multiclass_brier(y_valid.to_numpy(), proba, CLASS_LABELS))
        fold_macro_f1.append(float(f1_score(y_valid, pred, average="macro")))

    final_model = _build_model(exp.model_name, exp.params)
    final_model.fit(X_tv, y_tv)
    test_proba = _align_proba(final_model, X_test)
    test_pred = _predict_labels_from_proba(test_proba)

    result = {
        "exp_id": exp.exp_id,
        "feature_variant": exp.feature_variant,
        "model_name": exp.model_name,
        "params": exp.params,
        "cv_log_loss_mean": float(np.mean(fold_log_loss)),
        "cv_log_loss_std": float(np.std(fold_log_loss)),
        "cv_brier_mean": float(np.mean(fold_brier)),
        "cv_macro_f1_mean": float(np.mean(fold_macro_f1)),
        "test_log_loss": float(log_loss(y_test, test_proba, labels=CLASS_LABELS)),
        "test_brier": _multiclass_brier(y_test.to_numpy(), test_proba, CLASS_LABELS),
        "test_macro_f1": float(f1_score(y_test, test_pred, average="macro")),
        "model_obj": final_model,
    }
    return result


def _write_report(results_df: pd.DataFrame, best_row: pd.Series) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Experiments Comparison",
        "",
        "- validation: rolling-origin by season (time-aware)",
        "- leakage_policy: pre-match features only, blocked columns excluded",
        "- selection_metric: lowest `cv_log_loss_mean`",
        "",
        "## Ranking",
        "",
        "| rank | exp_id | feature_variant | model | params | cv_log_loss | cv_brier | cv_macro_f1 | test_log_loss | test_brier | test_macro_f1 | status |",
        "|---:|---|---|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]

    ranked = results_df.sort_values(
        ["cv_log_loss_mean", "cv_brier_mean", "test_log_loss"], ascending=[True, True, True]
    ).reset_index(drop=True)
    for i, row in ranked.iterrows():
        params_txt = json.dumps(row["params"], ensure_ascii=True)
        status_txt = "OK" if not row.get("error") else f"ERROR: {row['error']}"
        lines.append(
            f"| {i+1} | {row['exp_id']} | {row['feature_variant']} | {row['model_name']} | `{params_txt}` | "
            f"{row['cv_log_loss_mean']:.6f} | {row['cv_brier_mean']:.6f} | {row['cv_macro_f1_mean']:.6f} | "
            f"{row['test_log_loss']:.6f} | {row['test_brier']:.6f} | {row['test_macro_f1']:.6f} | {status_txt} |"
        )

    lines += [
        "",
        "## Principal Model",
        "",
        f"- exp_id: `{best_row['exp_id']}`",
        f"- model: `{best_row['model_name']}`",
        f"- feature_variant: `{best_row['feature_variant']}`",
        f"- params: `{json.dumps(best_row['params'], ensure_ascii=True)}`",
        f"- cv_log_loss_mean: `{best_row['cv_log_loss_mean']:.6f}`",
        f"- test_log_loss: `{best_row['test_log_loss']:.6f}`",
    ]

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _update_model_config(best_row: pd.Series) -> None:
    cfg = {}
    if MODEL_CONFIG_PATH.exists():
        with MODEL_CONFIG_PATH.open("r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}

    cfg["selected_principal_experiment"] = {
        "exp_id": best_row["exp_id"],
        "feature_variant": best_row["feature_variant"],
        "model_name": best_row["model_name"],
        "params": best_row["params"],
        "metric": "cv_log_loss_mean",
        "score": float(best_row["cv_log_loss_mean"]),
    }

    with MODEL_CONFIG_PATH.open("w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, sort_keys=False, allow_unicode=False)


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

    y_tv = train_valid_df["y_match"].astype(int)
    y_test = test_df["y_match"].astype(int)

    feature_variants_tv = _prepare_feature_variants(train_valid_df)
    feature_variants_test = _prepare_feature_variants(test_df)

    experiments = _build_experiments()
    results: list[dict[str, Any]] = []

    for exp in experiments:
        X_tv = feature_variants_tv[exp.feature_variant]
        X_test = feature_variants_test[exp.feature_variant]
        try:
            result = _evaluate_experiment(exp, X_tv, y_tv, X_test, y_test, splits)
            result["error"] = None
            print(
                f"{exp.exp_id} {exp.model_name} {exp.feature_variant} "
                f"cv_log_loss={result['cv_log_loss_mean']:.6f} test_log_loss={result['test_log_loss']:.6f}",
                flush=True,
            )
        except Exception as exc:
            result = {
                "exp_id": exp.exp_id,
                "feature_variant": exp.feature_variant,
                "model_name": exp.model_name,
                "params": exp.params,
                "cv_log_loss_mean": float("inf"),
                "cv_log_loss_std": float("inf"),
                "cv_brier_mean": float("inf"),
                "cv_macro_f1_mean": float("-inf"),
                "test_log_loss": float("inf"),
                "test_brier": float("inf"),
                "test_macro_f1": float("-inf"),
                "model_obj": None,
                "error": str(exc),
            }
            print(
                f"{exp.exp_id} {exp.model_name} {exp.feature_variant} ERROR={exc}",
                flush=True,
            )
        results.append(result)

    results_df = pd.DataFrame(results).sort_values(
        ["cv_log_loss_mean", "cv_brier_mean", "test_log_loss"], ascending=[True, True, True]
    )
    successful_df = results_df[results_df["error"].isna()].copy()
    if successful_df.empty:
        raise RuntimeError("All experiments failed.")

    best_row = successful_df.sort_values(
        ["cv_log_loss_mean", "cv_brier_mean", "test_log_loss"], ascending=[True, True, True]
    ).iloc[0]

    best_payload = {
        "principal": True,
        "exp_id": best_row["exp_id"],
        "model_name": best_row["model_name"],
        "feature_variant": best_row["feature_variant"],
        "params": best_row["params"],
        "feature_columns": feature_variants_tv[best_row["feature_variant"]].columns.tolist(),
        "class_labels": CLASS_LABELS,
        "cv_log_loss_mean": float(best_row["cv_log_loss_mean"]),
        "cv_brier_mean": float(best_row["cv_brier_mean"]),
        "cv_macro_f1_mean": float(best_row["cv_macro_f1_mean"]),
        "test_log_loss": float(best_row["test_log_loss"]),
        "test_brier": float(best_row["test_brier"]),
        "test_macro_f1": float(best_row["test_macro_f1"]),
        "model": best_row["model_obj"],
        "all_results": results_df.drop(columns=["model_obj"]).to_dict(orient="records"),
    }

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_payload, MODEL_PATH)

    _write_report(results_df.drop(columns=["model_obj"]), best_row)
    _update_model_config(best_row)

    print(f"saved={MODEL_PATH}")
    print(f"saved={REPORT_PATH}")
    print(f"best={best_row['exp_id']} {best_row['model_name']} {best_row['feature_variant']}")


if __name__ == "__main__":
    main()
