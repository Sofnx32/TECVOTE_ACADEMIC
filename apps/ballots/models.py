from django.db import models
from apps.elections.models import Election, Position, CandidateList


class Ballot(models.Model):
    """Boleta de una elección (puede haber una versión activa)."""
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name="ballots")
    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("election", "version")

    def __str__(self):
        return f"Ballot {self.election_id} v{self.version}"


class BallotPosition(models.Model):
    ballot = models.ForeignKey(Ballot, on_delete=models.CASCADE, related_name="ballot_positions")
    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name="ballot_positions")
    order = models.PositiveSmallIntegerField(default=1)

    class Meta:
        unique_together = ("ballot", "position")
        ordering = ["order"]


class BallotOption(models.Model):
    class OptionType(models.TextChoices):
        CANDIDATE_LIST = "CANDIDATE_LIST", "Lista"
        BLANK = "BLANK", "Blanco"
        NULL = "NULL", "Nulo"

    ballot_position = models.ForeignKey(BallotPosition, on_delete=models.CASCADE, related_name="options")
    option_type = models.CharField(max_length=20, choices=OptionType.choices, default=OptionType.CANDIDATE_LIST)
    candidate_list = models.ForeignKey(CandidateList, on_delete=models.CASCADE, blank=True, null=True)
    label = models.CharField(max_length=120)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["ballot_position", "candidate_list"],
                name="unique_candidate_list_per_ballot_position"
            )
        ]

    def __str__(self):
        return f"{self.option_type} - {self.label}"