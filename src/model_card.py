from datetime import datetime

from src.utils import ROOT, MODELS_DIR, REPORTS_DIR, load_json


def read_or_empty(path):
    if path.exists():
        return load_json(path)
    return {}


def main() -> None:
    metrics = read_or_empty(MODELS_DIR / "metrics.json")
    adversarial = read_or_empty(REPORTS_DIR / "adversarial_metrics.json")
    poisoning = read_or_empty(REPORTS_DIR / "poisoning_risk.json")
    drift = read_or_empty(REPORTS_DIR / "drift_metrics.json")
    supply = read_or_empty(REPORTS_DIR / "supply_chain.json")
    signing = read_or_empty(REPORTS_DIR / "model_signing.json")
    sbom = read_or_empty(REPORTS_DIR / "sbom.json")

    now = datetime.utcnow().isoformat() + "Z"

    content = f"""# Model Card: Breast Cancer Classifier

Generated at: {now}

## 1. Model Details

- Task: Binary classification (malignant vs benign)
- Algorithm: Logistic Regression (scikit-learn)
- Frameworks: scikit-learn, MLflow, DVC
- Repository: mlsecops-project

## 2. Data Description

- Source: `sklearn.datasets.load_breast_cancer`
- Number of samples: {sbom.get('dataset', {}).get('num_samples', 'N/A')}
- Number of features: {sbom.get('dataset', {}).get('num_features', 'N/A')}
- Number of classes: {sbom.get('dataset', {}).get('num_classes', 'N/A')}
- Preprocessing: simple train/test split with stratification

## 3. Evaluation Metrics

- Accuracy: {metrics.get('accuracy', 'N/A')}
- F1-score: {metrics.get('f1', 'N/A')}
- ROC-AUC: {metrics.get('roc_auc', 'N/A')}

## 4. Adversarial Robustness (OWASP ML01, MITRE Evasion)

- Clean accuracy: {adversarial.get('accuracy_clean', 'N/A')}
- FGSM accuracy: {adversarial.get('accuracy_fgsm', 'N/A')}
- PGD accuracy: {adversarial.get('accuracy_pgd', 'N/A')}
- Robustness score: {adversarial.get('robustness_score', 'N/A')}

Interpretation: robustness_score close to 1 indicates lower sensitivity to FGSM/PGD attacks.

## 5. Poisoning Risk (OWASP ML02, MITRE Poisoning)

- Outlier fraction: {poisoning.get('outlier_fraction', 'N/A')}
- Mean anomaly score: {poisoning.get('mean_anomaly_score', 'N/A')}
- Max anomaly score: {poisoning.get('max_anomaly_score', 'N/A')}
- Poisoning risk score: {poisoning.get('poisoning_risk_score', 'N/A')}

Higher poisoning risk score suggests potential anomalous training samples.

## 6. Drift Risk (OWASP ML08)

- Max PSI: {drift.get('max_psi', 'N/A')}
- Avg PSI: {drift.get('avg_psi', 'N/A')}
- Max JS divergence: {drift.get('max_js', 'N/A')}
- Avg JS divergence: {drift.get('avg_js', 'N/A')}
- Drift detected: {drift.get('drift_detected', 'N/A')}

PSI > 0.2 or JS > 0.1 indicates significant drift.

## 7. Supply Chain and SBOM (OWASP ML06-07, MITRE PoisonGPT)

- Banned packages OK: {supply.get('banned_packages_ok', 'N/A')}
- File hashes: {supply.get('file_hashes_sha256', {})}
- SBOM model hash: {sbom.get('model', {}).get('sha256', 'N/A')}
- SBOM HF model checksum: {sbom.get('hf_model', {}).get('checksum_sha256', 'N/A')}

Review SBOM for dependency integrity and potential supply chain risks.

## 8. Model Signing (OWASP ML10)

- Model path: {signing.get('model_path', 'N/A')}
- SHA256 hash: {signing.get('hash_sha256', 'N/A')}
- Signature (base64): {signing.get('signature_base64', 'N/A')}
- Public key path: {signing.get('public_key_path', 'N/A')}
- Signed at: {signing.get('signed_at', 'N/A')}

Signed models provide integrity and provenance guarantees.

## 9. Ethical Limitations

- Dataset represents a specific population and may not generalize globally.
- Model is for educational and demonstration purposes and must not be used as a sole diagnostic tool.
- Adversarial robustness, poisoning detection, and drift monitoring are simplified indicators and do not replace exhaustive security and safety assessments.
- LLM security tests use a dummy LLM and do not reflect real LLM behaviour.

## 10. Deployment and Monitoring

- CI/CD: Jenkins pipeline defined in `jenkins/Jenkinsfile`
- Experiment tracking: MLflow at `/mlflow`
- Data and model versioning: DVC in `dvc/`
- Security monitoring: scripts under `security/` and `src/security_audit.py`
"""

    path = ROOT / "model_card.md"
    path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
