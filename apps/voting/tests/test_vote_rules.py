from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

class VoteRulesTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_vote_requires_auth(self):
        r = self.client.post("/api/v1/votes/cast/", {}, format="json")
        self.assertIn(r.status_code, [401, 403])