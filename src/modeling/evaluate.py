from __future__ import annotations

from pathlib import Path

import joblib


REPORT_DIR = Path("artifacts/reports")
REPORT_PATH = REPORT_DIR / "evaluation_report.md"
MODEL_PATH = Path("artifacts/models/match_model.joblib")


def _exists(path: Path) -> str:
    return "yes" if path.exists() else "no"


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    principal_lines = [
        "- principal_model_available: no",
    ]
    if MODEL_PATH.exists():
        payload = joblib.load(MODEL_PATH)
        principal_lines = [
            "- principal_model_available: yes",
            f"- exp_id: {payload.get('exp_id', 'n/a')}",
            f"- model_name: {payload.get('model_name', 'n/a')}",
            f"- feature_variant: {payload.get('feature_variant', 'n/a')}",
            f"- cv_log_loss_mean: {payload.get('cv_log_loss_mean', 'n/a')}",
            f"- test_log_loss: {payload.get('test_log_loss', 'n/a')}",
        ]

    lines = [
        "# Evaluation Report",
        "",
        "## Principal Model",
        "",
        *principal_lines,
        "",
        "## Policy",
        "",
        "- inference_mode: preseason",
        "- calibration_in_main_pipeline: disabled (user decision)",
        "- validation_strategy: rolling-origin by season",
        "",
        "## Artifacts Check",
        "",
        f"- profiling_report: {_exists(REPORT_DIR / 'profiling_report.md')}",
        f"- leakage_gates_report: {_exists(REPORT_DIR / 'leakage_gates_report.md')}",
        f"- time_split_report: {_exists(REPORT_DIR / 'time_split_report.md')}",
        f"- experiments_comparison: {_exists(REPORT_DIR / 'experiments_comparison.md')}",
        "",
        "## Notes",
        "",
        "- Use `artifacts/reports/experiments_comparison.md` as the canonical model comparison table.",
    ]

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"saved={REPORT_PATH}")


if __name__ == "__main__":
    main()
