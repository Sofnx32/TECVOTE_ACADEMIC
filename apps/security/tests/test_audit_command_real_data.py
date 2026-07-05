from io import StringIO
from django.test import TestCase
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.academic.models import AcademicPeriod
from apps.elections.models import Election
from apps.security.services import create_audit_log

User = get_user_model()


class AuditCommandRealDataTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="admincmd@test.com", username="admincmd", institutional_id="CMD-1", password="Pass1234!", role="ADMIN"
        )
        self.period = AcademicPeriod.objects.create(
            name="2026-CMD", start_date=timezone.now().date(), end_date=timezone.now().date(), is_active=True
        )
        self.election = Election.objects.create(
            title="Audit Cmd Election",
            description="desc",
            election_type="UNIVERSITY",
            period=self.period,
            start_at=timezone.now(),
            end_at=timezone.now(),
            status="OPEN",
            created_by=self.user,
        )

    def test_verify_chain_with_real_logs(self):
        create_audit_log(actor=self.user, election=self.election, action="OPEN_ELECTION", metadata={"n": 1})
        create_audit_log(actor=self.user, election=self.election, action="CLOSE_ELECTION", metadata={"n": 2})

        out = StringIO()
        call_command("verify_audit_chain", stdout=out)
        txt = out.getvalue()
        self.assertIn("Checked 2", txt)