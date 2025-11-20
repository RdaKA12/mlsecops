from pathlib import Path

import numpy as np
import pandas as pd
import mlflow

from src.utils import (
    load_train_test_data,
    configure_mlflow,
    save_json,
    REPORTS_DIR,
)


def population_stability_index(expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    expected_counts, bin_edges = np.histogram(expected, bins=bins)
    actual_counts, _ = np.histogram(actual, bins=bin_edges)
    expected_perc = expected_counts.astype(float) / max(expected_counts.sum(), 1.0)
    actual_perc = actual_counts.astype(float) / max(actual_counts.sum(), 1.0)
    eps = 1e-6
    psi_values = (actual_perc - expected_perc) * np.log(
        (actual_perc + eps) / (expected_perc + eps)
    )
    return float(np.sum(psi_values))


def js_divergence(expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    p_counts, bin_edges = np.histogram(expected, bins=bins)
    q_counts, _ = np.histogram(actual, bins=bin_edges)
    p = p_counts.astype(float)
    q = q_counts.astype(float)
    if p.sum() == 0 or q.sum() == 0:
        return 0.0
    p = p / p.sum()
    q = q / q.sum()
    m = 0.5 * (p + q)
    eps = 1e-12
    kl_pm = np.sum(p * np.log((p + eps) / (m + eps)))
    kl_qm = np.sum(q * np.log((q + eps) / (m + eps)))
    return float(0.5 * (kl_pm + kl_qm))


def monitor_drift() -> dict:
    X_train, X_test, y_train, y_test = load_train_test_data()
    drift_stats = {}
    psi_values = []
    js_values = []
    for col in X_train.columns:
        expected = np.asarray(X_train[col])
        actual = np.asarray(X_test[col])
        psi = population_stability_index(expected, actual)
        js = js_divergence(expected, actual)
        drift_stats[col] = {"psi": psi, "js": js}
        psi_values.append(psi)
        js_values.append(js)
    max_psi = float(max(psi_values) if psi_values else 0.0)
    avg_psi = float(np.mean(psi_values) if psi_values else 0.0)
    max_js = float(max(js_values) if js_values else 0.0)
    avg_js = float(np.mean(js_values) if js_values else 0.0)
    drift_detected = bool(max_psi > 0.2 or max_js > 0.1)
    metrics = {
        "per_feature": drift_stats,
        "max_psi": max_psi,
        "avg_psi": avg_psi,
        "max_js": max_js,
        "avg_js": avg_js,
        "drift_detected": drift_detected,
    }
    path = REPORTS_DIR / "drift_metrics.json"
    save_json(path, metrics)
    configure_mlflow()
    with mlflow.start_run(run_name="drift_monitor"):
        mlflow.log_metric("max_psi", max_psi)
        mlflow.log_metric("avg_psi", avg_psi)
        mlflow.log_metric("max_js", max_js)
        mlflow.log_metric("avg_js", avg_js)
        mlflow.log_param("drift_detected", str(drift_detected))
        mlflow.log_artifact(str(path), artifact_path="drift_monitor")
    return metrics


def main() -> None:
    monitor_drift()


if __name__ == "__main__":
    main()
