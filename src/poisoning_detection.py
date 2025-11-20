import numpy as np
from sklearn.ensemble import IsolationForest
import mlflow

from src.utils import (
    load_train_test_data,
    configure_mlflow,
    save_json,
    REPORTS_DIR,
)


def detect_poisoning() -> dict:
    X_train, X_test, y_train, y_test = load_train_test_data()
    model = IsolationForest(
        n_estimators=200,
        contamination=0.05,
        random_state=42,
    )
    model.fit(X_train)
    scores = -model.decision_function(X_train)
    labels = model.predict(X_train)
    outlier_fraction = float(np.mean(labels == -1))
    mean_score = float(np.mean(scores))
    max_score = float(np.max(scores))
    risk_score = float(min(1.0, outlier_fraction * 2.0 + max_score / 10.0))
    metrics = {
        "outlier_fraction": outlier_fraction,
        "mean_anomaly_score": mean_score,
        "max_anomaly_score": max_score,
        "poisoning_risk_score": risk_score,
    }
    path = REPORTS_DIR / "poisoning_risk.json"
    save_json(path, metrics)
    configure_mlflow()
    with mlflow.start_run(run_name="poisoning_detection"):
        for k, v in metrics.items():
            mlflow.log_metric(k, v)
        mlflow.log_artifact(str(path), artifact_path="poisoning_detection")
    return metrics


def main() -> None:
    detect_poisoning()


if __name__ == "__main__":
    main()
