from django.test import TestCase
from rest_framework.test import APIClient

class ReceiptVerificationEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_not_found_receipt(self):
        r = self.client.get("/api/v1/public/verify-receipt/does-not-exist/")
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.json()["valid"], False)