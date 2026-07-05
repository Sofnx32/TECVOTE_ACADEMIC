from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.academic.models import AcademicPeriod
from apps.elections.models import Election

User = get_user_model()


class LifecycleGuardsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            email="admin2@test.com", username="admin2", institutional_id="ADM-2", password="Pass1234!", role="ADMIN"
        )
        self.student = User.objects.create_user(
            email="student2@test.com", username="student2", institutional_id="STD-2", password="Pass1234!", role="STUDENT"
        )
        self.period = AcademicPeriod.objects.create(
            name="2026-III",
            start_date=timezone.now().date(),
            end_date=timezone.now().date(),
            is_active=True,
        )
        self.election = Election.objects.create(
            title="Guards Election",
            description="desc",
            election_type="UNIVERSITY",
            period=self.period,
            start_at=timezone.now() - timezone.timedelta(hours=1),
            end_at=timezone.now() + timezone.timedelta(hours=1),
            status="OPEN",
            created_by=self.admin,
        )

    def test_certify_without_close_fails(self):
        self.client.force_authenticate(self.admin)
        r = self.client.post("/api/v1/election-lifecycle/certify/", {"election_id": self.election.id}, format="json")
        self.assertIn(r.status_code, [400, 409])

    def test_publish_without_certify_fails(self):
        self.client.force_authenticate(self.admin)
        r = self.client.post("/api/v1/election-lifecycle/publish/", {"election_id": self.election.id}, format="json")
        self.assertIn(r.status_code, [400, 409])

    def test_student_cannot_certify(self):
        self.client.force_authenticate(self.student)
        r = self.client.post("/api/v1/election-lifecycle/certify/", {"election_id": self.election.id}, format="json")
        self.assertIn(r.status_code, [403, 404])

    def test_student_cannot_publish(self):
        self.client.force_authenticate(self.student)
        r = self.client.post("/api/v1/election-lifecycle/publish/", {"election_id": self.election.id}, format="json")
        self.assertIn(r.status_code, [403, 404])