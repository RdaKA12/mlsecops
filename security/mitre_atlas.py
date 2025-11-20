from typing import Dict, Any

import numpy as np
import joblib
from sklearn.linear_model import LogisticRegression

from src.utils import (
    MODELS_DIR,
    REPORTS_DIR,
    load_train_test_data,
    load_json,
    ensure_dir,
    save_json,
)


def evasion_attack_simulation() -> Dict[str, Any]:
    path = REPORTS_DIR / "adversarial_metrics.json"
    if path.exists():
        metrics = load_json(path)
    else:
        metrics = {}
    drop = float(
        metrics.get("accuracy_clean", 0.0) - metrics.get("accuracy_fgsm", 0.0)
    )
    return {
        "technique": "ATLAS-Evasion-FGSM-PGD",
        "details": metrics,
        "accuracy_drop": drop,
    }


def poisoning_simulation() -> Dict[str, Any]:
    path = REPORTS_DIR / "poisoning_risk.json"
    if path.exists():
        metrics = load_json(path)
    else:
        metrics = {}
    return {
        "technique": "ATLAS-Poisoning",
        "details": metrics,
    }


def surrogate_model_extraction() -> Dict[str, Any]:
    X_train, X_test, y_train, y_test = load_train_test_data()
    target_model = joblib.load(MODELS_DIR / "model.pkl")
    target_proba = target_model.predict_proba(X_train)[:, 1]
    pseudo_labels = (target_proba > 0.5).astype(int)
    surrogate = LogisticRegression(max_iter=500, solver="liblinear")
    surrogate.fit(X_train, pseudo_labels)
    surrogate_proba = surrogate.predict_proba(X_train)[:, 1]
    fidelity = float(
        np.mean((surrogate_proba > 0.5).astype(int) == (target_proba > 0.5).astype(int))
    )
    return {
        "technique": "ATLAS-Model-Extraction",
        "surrogate_fidelity": fidelity,
    }


def backdoor_trigger_scanner() -> Dict[str, Any]:
    X_train, X_test, y_train, y_test = load_train_test_data()
    feature_means = np.mean(X_train.values, axis=0)
    feature_max = np.max(X_train.values, axis=0)
    ratios = feature_max / (feature_means + 1e-6)
    suspicious = bool(np.any(ratios > 10.0))
    return {
        "technique": "ATLAS-Backdoor-Scan",
        "suspicious_triggers": suspicious,
        "max_ratio": float(np.max(ratios)),
    }


def echo_leak_attack_test() -> Dict[str, Any]:
    payload = "<div>Public</div><span style=\"display:none\">Hidden Secret</span>"
    hidden_leak = "display:none" in payload.lower()
    return {
        "technique": "ATLAS-EchoLeak",
        "payload": payload,
        "hidden_leak_detected": bool(hidden_leak),
    }


def poison_gpt_supply_chain_simulation() -> Dict[str, Any]:
    path = REPORTS_DIR / "sbom.json"
    if path.exists():
        data = load_json(path)
    else:
        data = {}
    model_info = data.get("model", {})
    mismatch = False
    recorded_hash = model_info.get("sha256")
    if recorded_hash is None:
        mismatch = True
    return {
        "technique": "ATLAS-PoisonGPT-Supply-Chain",
        "model_info": model_info,
        "checksum_mismatch": bool(mismatch),
    }


def run() -> Dict[str, Any]:
    results = {
        "evasion": evasion_attack_simulation(),
        "poisoning": poisoning_simulation(),
        "surrogate_extraction": surrogate_model_extraction(),
        "backdoor_scan": backdoor_trigger_scanner(),
        "echo_leak": echo_leak_attack_test(),
        "poison_gpt_supply_chain": poison_gpt_supply_chain_simulation(),
    }
    path = REPORTS_DIR / "mitre_atlas.json"
    ensure_dir(path.parent)
    save_json(path, results)
    return results


def main() -> None:
    run()


if __name__ == "__main__":
    main()
