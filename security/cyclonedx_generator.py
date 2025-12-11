import json
import subprocess
import sys
from pathlib import Path

from src.utils import ROOT, REPORTS_DIR, ensure_dir


def generate_cyclonedx(output: Path = None) -> dict:
    if output is None:
        output = REPORTS_DIR / "sbom_cyclonedx.json"
    ensure_dir(output.parent)

    commands = [
        [
            "cyclonedx-py",
            "requirements",
            str(ROOT / "requirements.txt"),
            "-o",
            str(output),
            "--of",
            "JSON",
        ],
        [
            sys.executable,
            "-m",
            "cyclonedx_py",
            "requirements",
            str(ROOT / "requirements.txt"),
            "-o",
            str(output),
            "--of",
            "JSON",
        ],
    ]

    last_error = None
    for cmd in commands:
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            report = {"status": "ok", "generator": "cyclonedx", "output": str(output)}
            ensure_dir(output.parent)
            # The generator already wrote the file; also persist status
            (REPORTS_DIR / "sbom_cyclonedx_status.json").write_text(
                json.dumps(report, indent=2), encoding="utf-8"
            )
            return report
        except FileNotFoundError as e:
            last_error = str(e)
            continue
        except subprocess.CalledProcessError as e:
            last_error = e.stderr or str(e)
            continue

    # Fallback: write a minimal stub to keep pipeline going
    stub = {
        "status": "error",
        "message": "cyclonedx generator not available",
        "detail": last_error,
    }
    output.write_text(json.dumps(stub, indent=2), encoding="utf-8")
    (REPORTS_DIR / "sbom_cyclonedx_status.json").write_text(
        json.dumps(stub, indent=2), encoding="utf-8"
    )
    return stub


def main() -> None:
    generate_cyclonedx()


if __name__ == "__main__":
    main()
