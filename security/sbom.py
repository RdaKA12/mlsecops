import json
import platform
from hashlib import sha256
from pathlib import Path

try:
    import importlib.metadata as metadata
except ImportError:
    import importlib_metadata as metadata

from sklearn.datasets import load_breast_cancer

from src.utils import MODELS_DIR, REPORTS_DIR, hash_file, ensure_dir


def build_sbom() -> dict:
    pkgs = []
    for dist in metadata.distributions():
        name = dist.metadata.get("Name") or dist.metadata.get("Summary") or dist.metadata["Name"]
        version = dist.version
        h = sha256(f"{name}=={version}".encode("utf-8")).hexdigest()
        pkgs.append(
            {
                "name": name,
                "version": version,
                "hash": h,
            }
        )

    hf_model_id = "distilbert-base-uncased"
    hf_model_checksum = sha256(hf_model_id.encode("utf-8")).hexdigest()

    ds = load_breast_cancer()
    dataset_meta = {
        "name": "sklearn.breast_cancer",
        "num_samples": int(ds.data.shape[0]),
        "num_features": int(ds.data.shape[1]),
        "num_classes": int(len(ds.target_names)),
    }

    model_path = MODELS_DIR / "model.pkl"
    model_meta = {
        "path": str(model_path),
        "exists": bool(model_path.exists()),
        "sha256": hash_file(model_path) if model_path.exists() else None,
        "size_bytes": int(model_path.stat().st_size) if model_path.exists() else None,
    }

    sbom = {
        "generator": "mlsecops-project-sbom",
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "packages": pkgs,
        "hf_model": {
            "id": hf_model_id,
            "checksum_sha256": hf_model_checksum,
        },
        "dataset": dataset_meta,
        "model": model_meta,
    }
    return sbom


def main() -> None:
    sbom = build_sbom()
    path = REPORTS_DIR / "sbom.json"
    ensure_dir(path.parent)
    path.write_text(json.dumps(sbom, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
