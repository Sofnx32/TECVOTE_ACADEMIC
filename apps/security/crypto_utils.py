import base64
import hashlib
import json
from decouple import config
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


def canonical_json(data: dict) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sign_payload(payload: str) -> str:
    """
    Expects RSA private key in PEM format in env var ACTA_PRIVATE_KEY_PEM
    """
    private_key_pem = config("ACTA_PRIVATE_KEY_PEM", default="")
    if not private_key_pem:
        return ""

    private_key = serialization.load_pem_private_key(
        private_key_pem.encode("utf-8"),
        password=None,
    )

    signature = private_key.sign(
        payload.encode("utf-8"),
        padding.PKCS1v15(),
        hashes.SHA256(),
    )
    return base64.b64encode(signature).decode("utf-8")


def verify_signature(payload: str, signature_b64: str, public_key_pem: str) -> bool:
    try:
        public_key = serialization.load_pem_public_key(public_key_pem.encode("utf-8"))
        signature = base64.b64decode(signature_b64.encode("utf-8"))
        public_key.verify(
            signature,
            payload.encode("utf-8"),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        return True
    except Exception:
        return False