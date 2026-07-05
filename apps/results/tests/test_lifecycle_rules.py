from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

class LifecycleRulesTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.student = User.objects.create_user(
            email="s@test.com", username="s1", institutional_id="S1", password="Pass1234!", role="STUDENT"
        )

    def test_close_requires_admin(self):
        self.client.force_authenticate(user=self.student)
        r = self.client.post("/api/v1/election-lifecycle/close/", {"election_id": "00000000-0000-0000-0000-000000000000"}, format="json")
        self.assertIn(r.status_code, [403, 404])