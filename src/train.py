from pathlib import Path

import mlflow
import mlflow.sklearn
from sklearn.linear_model import LogisticRegression

from src.utils import (
    load_train_test_data,
    configure_mlflow,
    save_model,
    MODELS_DIR,
)


def train() -> Path:
    X_train, X_test, y_train, y_test = load_train_test_data()
    configure_mlflow()
    mlflow.sklearn.autolog()
    with mlflow.start_run(run_name="train_model"):
        model = LogisticRegression(max_iter=1000, solver="liblinear")
        model.fit(X_train, y_train)
        model_path = save_model(model)
        mlflow.sklearn.log_model(model, artifact_path="model")
    return model_path


def main() -> None:
    train()


if __name__ == "__main__":
    main()
