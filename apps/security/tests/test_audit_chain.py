from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.academic.models import AcademicPeriod
from apps.elections.models import Election
from apps.security.services import create_audit_log, build_audit_payload
from apps.security.crypto_utils import canonical_json, sha256_hex
from apps.security.models import AuditLog

User = get_user_model()


class AuditChainIntegrityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="admin@test.com",
            username="admin",
            institutional_id="ADM-1",
            password="Pass1234!",
            role="ADMIN",
        )
        self.period = AcademicPeriod.objects.create(
            name="2026-II",
            start_date=timezone.now().date(),
            end_date=timezone.now().date(),
            is_active=True,
        )
        self.election = Election.objects.create(
            title="Integrity Election",
            description="Test",
            election_type="UNIVERSITY",
            period=self.period,
            start_at=timezone.now(),
            end_at=timezone.now(),
            status="OPEN",
            created_by=self.user,
        )

    def test_hash_chain_is_consistent(self):
        a1 = create_audit_log(
            actor=self.user, election=self.election, action="OPEN_ELECTION", metadata={"step": 1}
        )
        a2 = create_audit_log(
            actor=self.user, election=self.election, action="CLOSE_ELECTION", metadata={"step": 2}
        )

        self.assertEqual(a2.previous_hash, a1.current_hash)

        payload2 = build_audit_payload(
            actor_id=a2.actor_id,
            election_id=a2.election_id,
            action=a2.action,
            ip_address=a2.ip_address,
            metadata=a2.metadata,
            previous_hash=a2.previous_hash,
        )
        self.assertEqual(a2.current_hash, sha256_hex(payload2))
    def test_detect_tampering(self):
        a1 = create_audit_log(
            actor=self.user, election=self.election, action="OPEN_ELECTION", metadata={"step": 1}
        )
        a1.metadata = {"step": 999}  # tamper
        a1.save(update_fields=["metadata"])

        payload = canonical_json({
            "actor_id": str(a1.actor_id) if a1.actor_id else None,
            "election_id": str(a1.election_id) if a1.election_id else None,
            "action": a1.action,
            "ip_address": a1.ip_address,
            "metadata": a1.metadata or {},
            "previous_hash": a1.previous_hash,
        })
        recomputed = sha256_hex(payload)
        self.assertNotEqual(a1.current_hash, recomputed)