import os
from pathlib import Path
import subprocess


def main() -> None:
    backend_uri = os.getenv("MLFLOW_BACKEND_STORE_URI", "sqlite:////mlflow/mlflow.db")
    artifact_root = os.getenv("MLFLOW_ARTIFACT_ROOT", "/mlflow_artifacts")
    port = os.getenv("MLFLOW_PORT", "5000")

    Path("/mlflow").mkdir(parents=True, exist_ok=True)
    Path(artifact_root).mkdir(parents=True, exist_ok=True)

    cmd = [
        "mlflow",
        "server",
        "--backend-store-uri",
        backend_uri,
        "--default-artifact-root",
        artifact_root,
        "--host",
        "0.0.0.0",
        "--port",
        port,
    ]
    subprocess.call(cmd)


if __name__ == "__main__":
    main()
