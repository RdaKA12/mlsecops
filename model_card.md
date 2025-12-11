# Model Card: Breast Cancer Classifier

Generated at: 2025-12-11T17:02:22.927172Z

## 1. Model Details

- Task: Binary classification (malignant vs benign)
- Algorithm: Logistic Regression (scikit-learn)
- Frameworks: scikit-learn, MLflow, DVC
- Repository: mlsecops-project

## 2. Data Description

- Source: `sklearn.datasets.load_breast_cancer`
- Number of samples: N/A
- Number of features: N/A
- Number of classes: N/A
- Preprocessing: simple train/test split with stratification

## 3. Evaluation Metrics

- Accuracy: 0.956140350877193
- F1-score: 0.9655172413793104
- ROC-AUC: 0.9957010582010581

## 4. Adversarial Robustness (OWASP ML01, MITRE Evasion)

- Clean accuracy: 0.956140350877193
- FGSM accuracy: 0.956140350877193
- PGD accuracy: 0.9385964912280702
- Robustness score: 0.9816513761467891

Interpretation: robustness_score close to 1 indicates lower sensitivity to FGSM/PGD attacks.

## 5. Poisoning Risk (OWASP ML02, MITRE Poisoning)

- Outlier fraction: 0.05054945054945055
- Mean anomaly score: -0.11590005390629389
- Max anomaly score: 0.14363837375194255
- Poisoning risk score: 0.11546273847409536

Higher poisoning risk score suggests potential anomalous training samples.

## 6. Drift Risk (OWASP ML08)

- Max PSI: 0.5928490116679558
- Avg PSI: 0.18732225936950647
- Max JS divergence: 0.030355944089736152
- Avg JS divergence: 0.011713616905713516
- Drift detected: True

PSI > 0.2 or JS > 0.1 indicates significant drift.

## 8. Fairness (Fairlearn)

- Sensitive feature: {'feature': 'mean radius', 'threshold': 13.68, 'groups': [0, 1]}
- Demographic parity diff: 0.6491228070175439
- Equalized odds diff: 0.11764705882352944
- Group metrics: {'0': {'accuracy': 1.0, 'f1': 1.0, 'selection_rate': 0.9649122807017544}, '1': {'accuracy': 0.9122807017543859, 'f1': 0.8571428571428571, 'selection_rate': 0.3157894736842105}}

Lower absolute parity/odds differences indicate better group fairness.

## 7. Supply Chain and SBOM (OWASP ML06-07, MITRE PoisonGPT)

- Banned packages OK: N/A
- File hashes: {}
- SBOM model hash: N/A
- SBOM HF model checksum: N/A
- CycloneDX SBOM: N/A

Review SBOM for dependency integrity and potential supply chain risks.

## 9. Model Signing (OWASP ML10)

- Model path: N/A
- SHA256 hash: N/A
- Signature (base64): N/A
- Public key path: N/A
- Signed at: N/A

Signed models provide integrity and provenance guarantees.

## 10. Giskard Quality Scan

- Status: error
- Issues found: N/A
- Tests run: N/A
- Artifacts: N/A

Review Giskard findings for robustness, data quality, and bias issues.

## 11. Governance (Credo AI)

- Status: N/A
- Detail: N/A
- Payload: reports/credo_payload.json

## 12. Ethical Limitations

- Dataset represents a specific population and may not generalize globally.
- Model is for educational and demonstration purposes and must not be used as a sole diagnostic tool.
- Adversarial robustness, poisoning detection, and drift monitoring are simplified indicators and do not replace exhaustive security and safety assessments.
- LLM security tests use a dummy LLM and do not reflect real LLM behaviour.

## 10. Deployment and Monitoring

- CI/CD: Jenkins pipeline defined in `jenkins/Jenkinsfile`
- Experiment tracking: MLflow at `/mlflow`
- Data and model versioning: DVC in `dvc/`
- Security monitoring: scripts under `security/` and `src/security_audit.py`
