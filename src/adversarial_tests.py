from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score
import mlflow

from src.utils import (
    load_train_test_data,
    load_model,
    configure_mlflow,
    save_json,
    REPORTS_DIR,
)


def generate_fgsm(model, X: pd.DataFrame, epsilon: float = 0.1) -> pd.DataFrame:
    w = model.coef_[0]
    noise = epsilon * np.sign(w)
    X_adv = X.values + noise
    return pd.DataFrame(X_adv, columns=X.columns)


def generate_pgd(
    model,
    X: pd.DataFrame,
    epsilon: float = 0.2,
    alpha: float = 0.05,
    num_iter: int = 5,
) -> pd.DataFrame:
    w = model.coef_[0]
    sign_w = np.sign(w)
    X_orig = X.values
    X_adv = X_orig.copy()
    for _ in range(num_iter):
        X_adv = X_adv + alpha * sign_w
        delta = np.clip(X_adv - X_orig, -epsilon, epsilon)
        X_adv = X_orig + delta
    return pd.DataFrame(X_adv, columns=X.columns)


def run_adversarial_tests() -> dict:
    X_train, X_test, y_train, y_test = load_train_test_data()
    model = load_model()
    y_clean = model.predict(X_test)
    acc_clean = float(accuracy_score(y_test, y_clean))
    X_fgsm = generate_fgsm(model, X_test, epsilon=0.1)
    X_pgd = generate_pgd(model, X_test, epsilon=0.2, alpha=0.05, num_iter=5)
    y_fgsm = model.predict(X_fgsm)
    y_pgd = model.predict(X_pgd)
    acc_fgsm = float(accuracy_score(y_test, y_fgsm))
    acc_pgd = float(accuracy_score(y_test, y_pgd))
    if acc_clean > 0:
        robustness_score = float(min(acc_fgsm, acc_pgd) / acc_clean)
    else:
        robustness_score = 0.0
    metrics = {
        "accuracy_clean": acc_clean,
        "accuracy_fgsm": acc_fgsm,
        "accuracy_pgd": acc_pgd,
        "robustness_score": robustness_score,
    }
    path = REPORTS_DIR / "adversarial_metrics.json"
    save_json(path, metrics)
    configure_mlflow()
    with mlflow.start_run(run_name="adversarial_tests"):
        for k, v in metrics.items():
            mlflow.log_metric(k, v)
        mlflow.log_artifact(str(path), artifact_path="adversarial")
    return metrics


def main() -> None:
    run_adversarial_tests()


if __name__ == "__main__":
    main()
