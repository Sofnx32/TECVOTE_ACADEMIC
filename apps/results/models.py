from django.db import models
from apps.elections.models import Election, Position
from apps.ballots.models import BallotOption


class Tally(models.Model):
    """Conteo por opción."""
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name="tallies")
    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name="tallies")
    option = models.ForeignKey(BallotOption, on_delete=models.CASCADE, related_name="tallies")
    votes_count = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("election", "position", "option")


class ElectionResult(models.Model):
    """Acta consolidada final."""
    election = models.OneToOneField(Election, on_delete=models.CASCADE, related_name="result")
    total_voters = models.PositiveIntegerField(default=0)
    total_votes_cast = models.PositiveIntegerField(default=0)
    turnout_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    blank_votes = models.PositiveIntegerField(default=0)
    null_votes = models.PositiveIntegerField(default=0)
    certified_at = models.DateTimeField(blank=True, null=True)
    published_at = models.DateTimeField(blank=True, null=True)
    report_pdf = models.FileField(upload_to="results/reports/", blank=True, null=True)
    report_hash = models.CharField(max_length=64, blank=True, default="")
    report_signature = models.TextField(blank=True, default="")
    def __str__(self):
        return f"Result election {self.election_id}"