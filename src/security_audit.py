from src.utils import REPORTS_DIR, ensure_dir, save_json
from security import owasp_ml_top10, owasp_llm_top10, mitre_atlas, supply_chain, sbom


def run_audit() -> dict:
    results = {}
    results["owasp_ml_top10"] = owasp_ml_top10.run()
    results["owasp_llm_top10"] = owasp_llm_top10.run()
    results["mitre_atlas"] = mitre_atlas.run()
    results["supply_chain"] = supply_chain.validate_supply_chain()
    results["sbom"] = sbom.build_sbom()
    path = REPORTS_DIR / "security_audit.json"
    ensure_dir(path.parent)
    save_json(path, results)
    return results


def main() -> None:
    run_audit()


if __name__ == "__main__":
    main()
