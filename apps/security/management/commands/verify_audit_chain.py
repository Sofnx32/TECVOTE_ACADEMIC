from django.core.management.base import BaseCommand
from apps.security.models import AuditLog
from apps.security.crypto_utils import canonical_json, sha256_hex


class Command(BaseCommand):
    help = "Verify audit hash chain integrity for all elections"

    def handle(self, *args, **options):
        logs = AuditLog.objects.order_by("election_id", "timestamp")
        by_election = {}
        for log in logs:
            by_election.setdefault(log.election_id, []).append(log)

        broken = 0
        checked = 0

        for election_id, entries in by_election.items():
            prev_hash = ""
            for e in entries:
                payload = canonical_json({
                    "actor_id": str(e.actor_id) if e.actor_id else None,
                    "election_id": str(e.election_id) if e.election_id else None,
                    "action": e.action,
                    "ip_address": e.ip_address,
                    "metadata": e.metadata or {},
                    "previous_hash": prev_hash,
                })
                expected = sha256_hex(payload)

                checked += 1
                if e.previous_hash != prev_hash or e.current_hash != expected:
                    broken += 1
                    self.stdout.write(self.style.ERROR(
                        f"[BROKEN] election={election_id} log={e.id}"
                    ))

                prev_hash = e.current_hash

        if broken == 0:
            self.stdout.write(self.style.SUCCESS(f"OK. Checked {checked} logs, no breaks."))
        else:
            self.stdout.write(self.style.ERROR(f"FAIL. Checked {checked}, broken={broken}."))