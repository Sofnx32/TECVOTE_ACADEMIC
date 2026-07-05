from apps.security.models import AuditLog
from .crypto_utils import canonical_json, sha256_hex, sign_payload


def build_audit_payload(*, actor_id, election_id, action, ip_address, metadata, previous_hash):
    return canonical_json({
        "actor_id": str(actor_id) if actor_id else None,
        "election_id": str(election_id) if election_id else None,
        "action": action,
        "ip_address": ip_address or None,
        "metadata": metadata or {},
        "previous_hash": previous_hash or "",
    })


def create_audit_log(*, actor, election, action: str, ip_address=None, metadata=None):
    metadata = metadata or {}
    prev = AuditLog.objects.filter(election=election).order_by("-timestamp").first()
    previous_hash = prev.current_hash if prev else ""

    payload = build_audit_payload(
        actor_id=getattr(actor, "id", None),
        election_id=getattr(election, "id", None),
        action=action,
        ip_address=ip_address,
        metadata=metadata,
        previous_hash=previous_hash,
    )
    current_hash = sha256_hex(payload)
    signature = sign_payload(current_hash)

    return AuditLog.objects.create(
        actor=actor,
        election=election,
        action=action,
        ip_address=ip_address,
        metadata=metadata,
        previous_hash=previous_hash,
        current_hash=current_hash,
        signature=signature,
    )