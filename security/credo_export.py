import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from src.utils import (
    ROOT,
    MODELS_DIR,
    REPORTS_DIR,
    load_json,
    hash_file,
    ensure_dir,
)


def _read(path: Path) -> Optional[Dict[str, Any]]:
    return load_json(path) if path.exists() else None


def build_payload() -> Dict[str, Any]:
    model_path = MODELS_DIR / "model.pkl"
    metrics_path = MODELS_DIR / "metrics.json"
    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "project": "mlsecops-project",
        "artifacts": {
            "model": {
                "path": str(model_path),
                "exists": model_path.exists(),
                "sha256": hash_file(model_path) if model_path.exists() else None,
            },
            "metrics": _read(metrics_path),
            "adversarial": _read(REPORTS_DIR / "adversarial_metrics.json"),
            "poisoning": _read(REPORTS_DIR / "poisoning_risk.json"),
            "drift": _read(REPORTS_DIR / "drift_metrics.json"),
            "security_audit": _read(REPORTS_DIR / "security_audit.json"),
            "owasp_ml_top10": _read(REPORTS_DIR / "owasp_ml_top10.json"),
            "owasp_llm_top10": _read(REPORTS_DIR / "owasp_llm_top10.json"),
            "mitre_atlas": _read(REPORTS_DIR / "mitre_atlas.json"),
            "supply_chain": _read(REPORTS_DIR / "supply_chain.json"),
            "sbom": _read(REPORTS_DIR / "sbom.json"),
            "sbom_cyclonedx": _read(REPORTS_DIR / "sbom_cyclonedx.json"),
            "fairness": _read(REPORTS_DIR / "fairness_metrics.json"),
            "giskard": _read(REPORTS_DIR / "giskard" / "giskard_status.json"),
            "giskard_scan": _read(REPORTS_DIR / "giskard" / "scan.json"),
            "model_card": str(ROOT / "model_card.md") if (ROOT / "model_card.md").exists() else None,
        },
    }
    return payload


def push_to_credo(payload: Dict[str, Any]) -> Dict[str, Any]:
    api_url = os.getenv("CREDO_API_URL")
    api_token = os.getenv("CREDO_API_TOKEN")
    endpoint = os.getenv("CREDO_API_ENDPOINT", "/api/v1/artifacts")

    if not api_url or not api_token:
        return {"status": "skipped", "reason": "CREDO_API_URL or CREDO_API_TOKEN not set"}

    try:
        import requests
    except ImportError as e:  # pragma: no cover - runtime guard
        return {"status": "error", "reason": "requests not installed", "detail": str(e)}

    url = api_url.rstrip("/") + endpoint
    headers = {"Authorization": f"Bearer {api_token}"}
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        return {"status": "ok", "code": resp.status_code, "url": url}
    except Exception as e:  # pragma: no cover - network guard
        return {"status": "error", "reason": "credo_api_push_failed", "detail": str(e), "url": url}


def main() -> None:
    ensure_dir(REPORTS_DIR)
    payload = build_payload()
    payload_path = REPORTS_DIR / "credo_payload.json"
    payload_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    status = push_to_credo(payload)
    status_path = REPORTS_DIR / "credo_status.json"
    status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
