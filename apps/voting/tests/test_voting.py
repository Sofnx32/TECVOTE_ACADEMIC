from django.test import TestCase
from rest_framework.test import APIClient

class VotingSmokeTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_health_home(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)