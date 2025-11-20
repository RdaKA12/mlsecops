from typing import Dict, Any

import numpy as np
import joblib

from src.utils import (
    MODELS_DIR,
    REPORTS_DIR,
    load_train_test_data,
    load_json,
    ensure_dir,
    save_json,
)


def ml01_adversarial_robustness() -> Dict[str, Any]:
    path = REPORTS_DIR / "adversarial_metrics.json"
    if path.exists():
        metrics = load_json(path)
    else:
        metrics = {}
    robustness = float(metrics.get("robustness_score", 0.0))
    level = "low"
    if robustness < 0.5:
        level = "high"
    elif robustness < 0.8:
        level = "medium"
    return {
        "risk": "ML01-Adversarial-Examples",
        "metrics": metrics,
        "risk_level": level,
    }


def ml02_poisoning_anomaly() -> Dict[str, Any]:
    path = REPORTS_DIR / "poisoning_risk.json"
    if path.exists():
        metrics = load_json(path)
    else:
        metrics = {}
    score = float(metrics.get("poisoning_risk_score", 0.0))
    level = "low"
    if score > 0.7:
        level = "high"
    elif score > 0.4:
        level = "medium"
    return {
        "risk": "ML02-Data-Poisoning",
        "metrics": metrics,
        "risk_level": level,
    }


def ml03_membership_inference() -> Dict[str, Any]:
    X_train, X_test, y_train, y_test = load_train_test_data()
    model = joblib.load(MODELS_DIR / "model.pkl")
    proba_train = model.predict_proba(X_train)[:, 1]
    proba_test = model.predict_proba(X_test)[:, 1]
    gap = float(np.mean(proba_train) - np.mean(proba_test))
    risk_score = float(min(1.0, max(0.0, gap)))
    level = "low"
    if risk_score > 0.3:
        level = "medium"
    if risk_score > 0.6:
        level = "high"
    return {
        "risk": "ML03-Membership-Inference",
        "avg_confidence_gap": gap,
        "risk_score": risk_score,
        "risk_level": level,
    }


def ml04_model_inversion() -> Dict[str, Any]:
    X_train, X_test, y_train, y_test = load_train_test_data()
    model = joblib.load(MODELS_DIR / "model.pkl")
    proba = model.predict_proba(X_train)[:, 1]
    eps = 1e-12
    entropy = -np.mean(
        proba * np.log(proba + eps) + (1 - proba) * np.log(1 - proba + eps)
    )
    inversion_risk = float(max(0.0, 1.0 - entropy))
    level = "low"
    if inversion_risk > 0.5:
        level = "medium"
    if inversion_risk > 0.8:
        level = "high"
    return {
        "risk": "ML04-Model-Inversion",
        "entropy": float(entropy),
        "inversion_risk": inversion_risk,
        "risk_level": level,
    }


def ml05_model_extraction_pattern() -> Dict[str, Any]:
    log_path = REPORTS_DIR / "prediction_log.json"
    if log_path.exists():
        log = load_json(log_path)
        num_queries = int(log.get("num_queries", 0))
        unique_inputs = int(log.get("unique_inputs", 0))
    else:
        num_queries = 0
        unique_inputs = 0
    if num_queries == 0:
        extraction_score = 0.0
    else:
        extraction_score = float(min(1.0, num_queries / 1000.0))
    return {
        "risk": "ML05-Model-Extraction",
        "num_queries": num_queries,
        "unique_inputs": unique_inputs,
        "extraction_risk_score": extraction_score,
    }


def ml06_ml07_supply_chain() -> Dict[str, Any]:
    path = REPORTS_DIR / "supply_chain.json"
    if path.exists():
        data = load_json(path)
    else:
        data = {}
    banned_ok = bool(data.get("banned_packages_ok", True))
    level = "low" if banned_ok else "high"
    return {
        "risk": "ML06-07-Supply-Chain",
        "details": data,
        "risk_level": level,
    }


def ml08_drift_detection() -> Dict[str, Any]:
    path = REPORTS_DIR / "drift_metrics.json"
    if path.exists():
        data = load_json(path)
    else:
        data = {}
    drift = bool(data.get("drift_detected", False))
    level = "low"
    if drift:
        level = "high"
    return {
        "risk": "ML08-Data-Drift",
        "details": data,
        "risk_level": level,
    }


def ml09_output_integrity() -> Dict[str, Any]:
    path = REPORTS_DIR / "baseline_predictions.json"
    if path.exists():
        data = load_json(path)
        y_pred = np.asarray(data.get("y_pred", []))
    else:
        data = {}
        y_pred = np.asarray([])
    integrity_hash = None
    if y_pred.size > 0:
        integrity_hash = int(np.sum(y_pred) % 2)
    return {
        "risk": "ML09-Output-Integrity",
        "baseline_size": int(y_pred.size),
        "integrity_indicator": integrity_hash,
    }


def ml10_model_signing() -> Dict[str, Any]:
    path = REPORTS_DIR / "model_signing.json"
    if path.exists():
        data = load_json(path)
        signed = True
    else:
        data = {}
        signed = False
    level = "high" if not signed else "low"
    return {
        "risk": "ML10-Model-Checkpoint-Signing",
        "signed": signed,
        "details": data,
        "risk_level": level,
    }


def run() -> Dict[str, Any]:
    results = {
        "ML01": ml01_adversarial_robustness(),
        "ML02": ml02_poisoning_anomaly(),
        "ML03": ml03_membership_inference(),
        "ML04": ml04_model_inversion(),
        "ML05": ml05_model_extraction_pattern(),
        "ML06_07": ml06_ml07_supply_chain(),
        "ML08": ml08_drift_detection(),
        "ML09": ml09_output_integrity(),
        "ML10": ml10_model_signing(),
    }
    path = REPORTS_DIR / "owasp_ml_top10.json"
    ensure_dir(path.parent)
    save_json(path, results)
    return results


def main() -> None:
    run()


if __name__ == "__main__":
    main()
