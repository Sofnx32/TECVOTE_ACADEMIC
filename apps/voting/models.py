import uuid
from django.db import models
from django.conf import settings
from apps.elections.models import Election
from apps.ballots.models import BallotOption


class VotingSession(models.Model):
    """Sesión de emisión de voto por elector."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name="voting_sessions")
    voter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="voting_sessions")
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    is_successful = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["election", "voter"]),
        ]


class Vote(models.Model):
    """
    Voto emitido (idealmente cifrado o tokenizado).
    one voter -> one election
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name="votes")
    voter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="votes")
    session = models.OneToOneField(VotingSession, on_delete=models.PROTECT, related_name="vote")
    cast_at = models.DateTimeField(auto_now_add=True)

    receipt_code = models.CharField(max_length=64, unique=True)   # comprobante verificable
    encrypted_payload = models.TextField()                         # contenido cifrado del voto
    payload_hash = models.CharField(max_length=128, db_index=True) # integridad

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["election", "voter"], name="unique_vote_per_voter_per_election")
        ]


class VoteSelection(models.Model):
    """
    Desnormalización controlada para conteo rápido (si política lo permite).
    Si anonimato estricto: separar identidad y selección en otra DB o usar mixnet.
    """
    vote = models.ForeignKey(Vote, on_delete=models.CASCADE, related_name="selections")
    ballot_option = models.ForeignKey(BallotOption, on_delete=models.PROTECT, related_name="selections")

    class Meta:
        unique_together = ("vote", "ballot_option")