import argparse
import base64
import datetime
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from src.utils import hash_file, REPORTS_DIR, ensure_dir, save_json


def generate_keys(private_key_path: Path, public_key_path: Path) -> None:
    ensure_dir(private_key_path.parent)
    ensure_dir(public_key_path.parent)
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_key = private_key.public_key()
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    private_key_path.write_bytes(private_bytes)
    public_key_path.write_bytes(public_bytes)


def sign_model(model_path: Path, private_key_path: Path, signature_path: Path) -> dict:
    digest = hash_file(model_path)
    private_key = serialization.load_pem_private_key(
        private_key_path.read_bytes(), password=None
    )
    signature = private_key.sign(
        digest.encode("utf-8"),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )
    ensure_dir(signature_path.parent)
    signature_path.write_bytes(signature)
    meta = {
        "model_path": str(model_path),
        "hash_sha256": digest,
        "signature_base64": base64.b64encode(signature).decode("utf-8"),
        "private_key_path": str(private_key_path),
        "public_key_path": str(
            private_key_path.parent / (private_key_path.stem + ".pub.pem")
        ),
        "signed_at": datetime.datetime.utcnow().isoformat() + "Z",
    }
    report_path = REPORTS_DIR / "model_signing.json"
    save_json(report_path, meta)
    return meta


def verify_model(model_path: Path, public_key_path: Path, signature_path: Path) -> bool:
    digest = hash_file(model_path)
    signature = signature_path.read_bytes()
    public_key = serialization.load_pem_public_key(public_key_path.read_bytes())
    try:
        public_key.verify(
            signature,
            digest.encode("utf-8"),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )
        return True
    except Exception:
        return False


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    gen_parser = subparsers.add_parser("generate-keys")
    gen_parser.add_argument(
        "--private-key",
        type=str,
        default="security/keys/private_key.pem",
    )
    gen_parser.add_argument(
        "--public-key",
        type=str,
        default="security/keys/private_key.pub.pem",
    )

    sign_parser = subparsers.add_parser("sign")
    sign_parser.add_argument(
        "--model-path",
        type=str,
        default="dvc/models/model.pkl",
    )
    sign_parser.add_argument(
        "--private-key",
        type=str,
        default="security/keys/private_key.pem",
    )
    sign_parser.add_argument(
        "--signature-path",
        type=str,
        default="security/signatures/model.sig",
    )

    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument(
        "--model-path",
        type=str,
        default="dvc/models/model.pkl",
    )
    verify_parser.add_argument(
        "--public-key",
        type=str,
        default="security/keys/private_key.pub.pem",
    )
    verify_parser.add_argument(
        "--signature-path",
        type=str,
        default="security/signatures/model.sig",
    )

    args = parser.parse_args()

    if args.command == "generate-keys":
        generate_keys(Path(args.private_key), Path(args.public_key))
    elif args.command == "sign":
        sign_model(Path(args.model_path), Path(args.private_key), Path(args.signature_path))
    elif args.command == "verify":
        valid = verify_model(Path(args.model_path), Path(args.public_key), Path(args.signature_path))
        result = {"model_path": args.model_path, "signature_valid": bool(valid)}
        report_path = REPORTS_DIR / "model_signature_verification.json"
        save_json(report_path, result)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
