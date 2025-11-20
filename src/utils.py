import json
import os
import hashlib
from pathlib import Path
from typing import Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
import mlflow


ROOT = Path(__file__).resolve().parents[1]
DVC_DIR = ROOT / "dvc"
DATA_DIR = DVC_DIR / "data"
MODELS_DIR = DVC_DIR / "models"
REPORTS_DIR = ROOT / "reports"
LOGS_DIR = ROOT / "logs"


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_json(path: Path, data: dict) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def configure_mlflow() -> None:
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
    experiment_name = os.getenv("MLFLOW_EXPERIMENT_NAME", "mlsecops-demo")
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment_name)


def get_data() -> Tuple[pd.DataFrame, str]:
    ds = load_breast_cancer(as_frame=True)
    df = ds.frame
    df = df.rename(columns={"target": "label"})
    return df, "label"


def prepare_train_test(test_size: float = 0.2, random_state: int = 42):
    df, target_col = get_data()
    X = df.drop(columns=[target_col])
    y = df[target_col]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, stratify=y, random_state=random_state
    )
    ensure_dir(DATA_DIR)
    train_df = pd.concat([X_train, y_train], axis=1)
    test_df = pd.concat([X_test, y_test], axis=1)
    train_df.to_csv(DATA_DIR / "train.csv", index=False)
    test_df.to_csv(DATA_DIR / "test.csv", index=False)
    return X_train, X_test, y_train, y_test


def load_train_test_data():
    train_path = DATA_DIR / "train.csv"
    test_path = DATA_DIR / "test.csv"
    if not train_path.exists() or not test_path.exists():
        return prepare_train_test()
    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(test_path)
    target_col = "label"
    X_train = train_df.drop(columns=[target_col])
    y_train = train_df[target_col]
    X_test = test_df.drop(columns=[target_col])
    y_test = test_df[target_col]
    return X_train, X_test, y_train, y_test


def save_model(model, path: Path = None) -> Path:
    ensure_dir(MODELS_DIR)
    if path is None:
        path = MODELS_DIR / "model.pkl"
    joblib.dump(model, path)
    return path


def load_model(path: Path = None):
    if path is None:
        path = MODELS_DIR / "model.pkl"
    return joblib.load(path)


def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()
