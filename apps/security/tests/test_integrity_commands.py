from django.test import TestCase
from django.core.management import call_command

class IntegrityCommandTests(TestCase):
    def test_verify_chain_command_runs(self):
        call_command("verify_audit_chain")