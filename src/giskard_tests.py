from pathlib import Path
from typing import Any, Dict

import numpy as np

from src.utils import (
    load_train_test_data,
    load_model,
    save_json,
    ensure_dir,
    REPORTS_DIR,
)


def _default_feature_types(columns) -> Dict[str, str]:
    return {c: "numeric" for c in columns}


def run_giskard_scan() -> Dict[str, Any]:
    reports_dir = REPORTS_DIR / "giskard"
    ensure_dir(reports_dir)

    try:
        from giskard import Dataset, Model, scan
    except ImportError as e:  # pragma: no cover - runtime guard
        result = {
            "status": "error",
            "message": "giskard not installed",
            "detail": str(e),
        }
        save_json(reports_dir / "giskard_status.json", result)
        return result

    X_train, X_test, y_train, y_test = load_train_test_data()
    model = load_model()

    def predict_fn(df):
        if hasattr(model, "predict_proba"):
            return model.predict_proba(df)[:, 1]
        preds = model.predict(df)
        if preds.ndim == 1:
            return preds
        return preds[:, 0]

    giskard_dataset = Dataset(
        df=X_test,
        target=y_test,
        column_types=_default_feature_types(X_test.columns),
        name="breast_cancer_test",
    )
    giskard_model = Model(
        model=predict_fn,
        model_type="classification",
        feature_names=list(X_test.columns),
        classification_labels=[0, 1],
        name="logreg_classifier",
    )

    scan_result = scan(model=giskard_model, dataset=giskard_dataset)

    # Persist artifacts
    scan_json_path = reports_dir / "scan.json"
    scan_html_path = reports_dir / "scan.html"
    scan_result.to_json(str(scan_json_path))
    try:
        scan_result.to_html(str(scan_html_path))
    except Exception:
        # Some versions may not support HTML export; ignore.
        pass

    summary = {
        "status": "ok",
        "issues_found": len(getattr(scan_result, "issues", []) or []),
        "tests_run": len(getattr(scan_result, "tests", []) or []),
        "artifacts": {
            "json": str(scan_json_path),
            "html": str(scan_html_path),
        },
    }
    save_json(reports_dir / "giskard_status.json", summary)
    return summary


def main() -> None:
    run_giskard_scan()


if __name__ == "__main__":
    main()
