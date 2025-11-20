import json
import subprocess
from hashlib import sha256
from pathlib import Path

from src.utils import ROOT, REPORTS_DIR, ensure_dir, save_json


BANNED_PACKAGES = {"malicious-lib", "suspicious-pkg"}


def compute_hash(path: Path) -> str:
    h = sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def list_installed_packages() -> list:
    try:
        result = subprocess.run(
            ["pip", "list", "--format", "json"],
            capture_output=True,
            check=True,
            text=True,
        )
        return json.loads(result.stdout)
    except Exception:
        return []


def validate_supply_chain() -> dict:
    files_to_hash = [
        ROOT / "requirements.txt",
        ROOT / "docker" / "trainer.Dockerfile",
        ROOT / "docker" / "mlflow.Dockerfile",
        ROOT / "jenkins" / "Jenkinsfile",
    ]
    hashes = {}
    for path in files_to_hash:
        if path.exists():
            hashes[str(path)] = compute_hash(path)

    pkgs = list_installed_packages()
    banned_found = [p for p in pkgs if p.get("name") in BANNED_PACKAGES]

    result = {
        "file_hashes_sha256": hashes,
        "banned_packages_found": banned_found,
        "banned_packages_ok": len(banned_found) == 0,
    }
    return result


def main() -> None:
    report = validate_supply_chain()
    path = REPORTS_DIR / "supply_chain.json"
    ensure_dir(path.parent)
    save_json(path, report)


if __name__ == "__main__":
    main()
