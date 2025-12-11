from pathlib import Path
from typing import Any, Dict, Tuple

import numpy as np

from src.utils import (
    load_train_test_data,
    load_model,
    configure_mlflow,
    save_json,
    REPORTS_DIR,
)


def _build_sensitive_feature(X) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Derive a demo-sensitive feature without changing the dataset schema.
    Uses the first numeric column and splits by its median to create two groups.
    """
    col = X.columns[0]
    median = float(np.median(X[col]))
    sensitive = (X[col] >= median).astype(int).to_numpy()
    meta = {"feature": col, "threshold": median, "groups": [0, 1]}
    return sensitive, meta


def run_fairness() -> Dict[str, Any]:
    try:
        from fairlearn.metrics import (
            MetricFrame,
            selection_rate,
            demographic_parity_difference,
            equalized_odds_difference,
        )
        from sklearn.metrics import accuracy_score, f1_score
    except ImportError as e:  # pragma: no cover - runtime guard
        error_report = {
            "status": "error",
            "message": "fairlearn not installed",
            "detail": str(e),
        }
        path = REPORTS_DIR / "fairness_metrics.json"
        save_json(path, error_report)
        return error_report

    X_train, X_test, y_train, y_test = load_train_test_data()
    model = load_model()

    y_pred = model.predict(X_test)
    sensitive, sensitive_meta = _build_sensitive_feature(X_test)

    frame = MetricFrame(
        metrics={
            "accuracy": accuracy_score,
            "f1": f1_score,
            "selection_rate": selection_rate,
        },
        y_true=y_test,
        y_pred=y_pred,
        sensitive_features=sensitive,
    )

    dp_diff = float(
        demographic_parity_difference(
            y_true=y_test, y_pred=y_pred, sensitive_features=sensitive
        )
    )
    eod_diff = float(
        equalized_odds_difference(
            y_true=y_test, y_pred=y_pred, sensitive_features=sensitive
        )
    )

    # Aggregate
    result = {
        "status": "ok",
        "sensitive_feature": sensitive_meta,
        "overall": {
            "accuracy": float(frame.overall["accuracy"]),
            "f1": float(frame.overall["f1"]),
            "selection_rate": float(frame.overall["selection_rate"]),
        },
        "by_group": {
            str(group): {
                "accuracy": float(frame.by_group["accuracy"].loc[group]),
                "f1": float(frame.by_group["f1"].loc[group]),
                "selection_rate": float(frame.by_group["selection_rate"].loc[group]),
            }
            for group in frame.by_group.index
        },
        "fairness": {
            "demographic_parity_difference": dp_diff,
            "equalized_odds_difference": eod_diff,
        },
    }

    path = REPORTS_DIR / "fairness_metrics.json"
    save_json(path, result)

    # Optional MLflow logging for traceability
    configure_mlflow()
    try:
        import mlflow

        with mlflow.start_run(run_name="fairlearn_fairness"):
            for k, v in result["overall"].items():
                mlflow.log_metric(f"fairness_overall_{k}", v)
            for group, metrics in result["by_group"].items():
                for k, v in metrics.items():
                    mlflow.log_metric(f"fairness_group_{group}_{k}", v)
            mlflow.log_metric("fairness_demographic_parity_diff", dp_diff)
            mlflow.log_metric("fairness_equalized_odds_diff", eod_diff)
            mlflow.log_artifact(str(path), artifact_path="fairness")
    except Exception:
        # Do not fail the pipeline if MLflow is not reachable.
        pass

    return result


def main() -> None:
    run_fairness()


if __name__ == "__main__":
    main()
