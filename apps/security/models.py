import uuid
from django.db import models
from django.conf import settings
from apps.elections.models import Election


class AuditLog(models.Model):
    class ActionType(models.TextChoices):
        LOGIN = "LOGIN", "Login"
        VERIFY_2FA = "VERIFY_2FA", "Verify 2FA"
        CREATE_ELECTION = "CREATE_ELECTION", "Create election"
        OPEN_ELECTION = "OPEN_ELECTION", "Open election"
        CAST_VOTE = "CAST_VOTE", "Cast vote"
        CLOSE_ELECTION = "CLOSE_ELECTION", "Close election"
        CERTIFY_RESULT = "CERTIFY_RESULT", "Certify result"
        PUBLISH_RESULT = "PUBLISH_RESULT", "Publish result"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    election = models.ForeignKey(Election, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=40, choices=ActionType.choices)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)

    # enterprise integrity fields
    previous_hash = models.CharField(max_length=64, blank=True, default="")
    current_hash = models.CharField(max_length=64, blank=True, default="")
    signature = models.TextField(blank=True, default="")  # base64 signature

    class Meta:
        indexes = [
            models.Index(fields=["action", "timestamp"]),
            models.Index(fields=["election", "timestamp"]),
        ]

class OneTimeToken(models.Model):
    """Token de un solo uso para habilitar voto o paso crítico."""
    token = models.CharField(max_length=128, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ottokens")
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name="ottokens")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(blank=True, null=True)

    @property
    def is_used(self):
        return self.used_at is not None