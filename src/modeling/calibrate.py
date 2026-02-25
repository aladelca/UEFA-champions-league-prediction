from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import log_loss

from src.modeling.train_match_model import CLASS_LABELS, _build_candidate_models
from src.modeling.split_time import split_train_test_by_season
from src.utils.io import read_dataframe, resolve_existing_data_path


FEATURES_PATH = Path("data/interim/feature_store_pre_match.parquet")
MODEL_PATH = Path("artifacts/models/match_model.joblib")
CALIBRATOR_PATH = Path("artifacts/models/calibrator.joblib")
REPORT_PATH = Path("artifacts/reports/evaluation_report.md")


def _append_calibration_report(lines: list[str]) -> None:
    if not REPORT_PATH.exists():
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text("# Evaluation Report\n", encoding="utf-8")

    with REPORT_PATH.open("a", encoding="utf-8") as f:
        f.write("\n## Calibration\n\n")
        for line in lines:
            f.write(f"- {line}\n")


def main() -> None:
    if not MODEL_PATH.exists():
        from src.modeling.train_match_model import main as train_main

        train_main()

    if resolve_existing_data_path(FEATURES_PATH) is None:
        from src.features.build_pre_match_features import main as build_features_main

        build_features_main()

    payload = joblib.load(MODEL_PATH)
    model_name = payload["model_name"]
    feature_cols = payload["feature_columns"]
    feature_variant = payload.get("feature_variant")

    df = read_dataframe(FEATURES_PATH, parse_dates=["Date"])
    df = df.sort_values(["Date", "match_id"]).reset_index(drop=True)
    train_valid_df, _ = split_train_test_by_season(df, test_season=2021, season_col="season")
    train_valid_df = train_valid_df.sort_values(["Date", "match_id"]).reset_index(drop=True)

    if all(col in train_valid_df.columns for col in feature_cols):
        feature_matrix = train_valid_df[feature_cols].copy()
    else:
        from src.modeling.run_experiments import _prepare_feature_variants

        variants = _prepare_feature_variants(train_valid_df)
        if feature_variant is None or feature_variant not in variants:
            raise ValueError(
                "Model requires engineered feature variant, but feature_variant is missing in payload."
            )
        feature_matrix = variants[feature_variant]
        if not all(col in feature_matrix.columns for col in feature_cols):
            missing = [c for c in feature_cols if c not in feature_matrix.columns]
            raise ValueError(f"Missing engineered feature columns for calibration: {missing}")

    seasons = sorted(int(s) for s in train_valid_df["season"].unique())
    calibration_season = seasons[-1]

    fit_df = train_valid_df[train_valid_df["season"] < calibration_season].copy()
    calib_df = train_valid_df[train_valid_df["season"] == calibration_season].copy()

    if fit_df.empty or calib_df.empty:
        joblib.dump(payload, CALIBRATOR_PATH)
        _append_calibration_report(
            [
                "status: skipped",
                "reason: insufficient temporal split for calibration holdout",
            ]
        )
        print(f"saved={CALIBRATOR_PATH}")
        return

    models = _build_candidate_models()
    if model_name not in models:
        raise ValueError(f"Selected model '{model_name}' is not available for calibration.")
    base_model = models[model_name]

    X_fit = feature_matrix.loc[fit_df.index, feature_cols]
    y_fit = fit_df["y_match"].astype(int)
    X_cal = feature_matrix.loc[calib_df.index, feature_cols]
    y_cal = calib_df["y_match"].astype(int)

    base_model.fit(X_fit, y_fit)
    raw_proba = base_model.predict_proba(X_cal)
    raw_logloss = float(log_loss(y_cal, raw_proba, labels=CLASS_LABELS))

    calibrator = CalibratedClassifierCV(estimator=models[model_name], method="sigmoid", cv=3)
    calibrator.fit(X_fit, y_fit)
    cal_proba = calibrator.predict_proba(X_cal)
    calibrated_logloss = float(log_loss(y_cal, cal_proba, labels=CLASS_LABELS))

    calibrator_payload = {
        "model_name": model_name,
        "feature_columns": feature_cols,
        "class_labels": CLASS_LABELS,
        "calibration_method": "sigmoid",
        "calibration_season": calibration_season,
        "raw_log_loss_on_calibration": raw_logloss,
        "calibrated_log_loss_on_calibration": calibrated_logloss,
        "estimator": calibrator,
    }

    CALIBRATOR_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(calibrator_payload, CALIBRATOR_PATH)

    _append_calibration_report(
        [
            "status: completed",
            f"method: sigmoid (CalibratedClassifierCV, cv=3 on train window)",
            f"calibration_season: {calibration_season}",
            f"raw_log_loss: {raw_logloss:.6f}",
            f"calibrated_log_loss: {calibrated_logloss:.6f}",
        ]
    )
    print(f"saved={CALIBRATOR_PATH}")
    print(f"calibration_season={calibration_season}")
    print(f"raw_log_loss={raw_logloss:.6f}")
    print(f"calibrated_log_loss={calibrated_logloss:.6f}")


if __name__ == "__main__":
    main()
