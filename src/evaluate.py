from pathlib import Path

import numpy as np
import mlflow
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score

from src.utils import (
    load_train_test_data,
    load_model,
    configure_mlflow,
    save_json,
    MODELS_DIR,
    REPORTS_DIR,
)


def evaluate() -> dict:
    X_train, X_test, y_train, y_test = load_train_test_data()
    model = load_model()
    y_pred = model.predict(X_test)
    if hasattr(model, "predict_proba"):
        y_proba = model.predict_proba(X_test)[:, 1]
    else:
        y_proba = y_pred.astype(float)
    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "f1": float(f1_score(y_test, y_pred)),
        "roc_auc": float(roc_auc_score(y_test, y_proba)),
    }
    metrics_path = MODELS_DIR / "metrics.json"
    save_json(metrics_path, metrics)
    baseline_path = REPORTS_DIR / "baseline_predictions.json"
    baseline = {
        "y_true": list(map(int, np.asarray(y_test))),
        "y_pred": list(map(int, np.asarray(y_pred))),
        "y_proba": list(map(float, np.asarray(y_proba))),
    }
    save_json(baseline_path, baseline)
    configure_mlflow()
    with mlflow.start_run(run_name="evaluate_model"):
        for k, v in metrics.items():
            mlflow.log_metric(k, v)
        mlflow.log_artifact(str(metrics_path), artifact_path="evaluation")
    return metrics


def main() -> None:
    evaluate()


if __name__ == "__main__":
    main()
