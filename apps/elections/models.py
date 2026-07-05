from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.academic.models import AcademicPeriod, Faculty, Program


class Election(models.Model):
    class ElectionType(models.TextChoices):
        UNIVERSITY = "UNIVERSITY", "Universitaria"
        FACULTY = "FACULTY", "Facultad"
        PROGRAM = "PROGRAM", "Carrera/Programa"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Borrador"
        SCHEDULED = "SCHEDULED", "Programada"
        OPEN = "OPEN", "Abierta"
        CLOSED = "CLOSED", "Cerrada"
        CERTIFIED = "CERTIFIED", "Certificada"
        PUBLISHED = "PUBLISHED", "Publicada"

    title = models.CharField(max_length=255)
    description = models.TextField()
    election_type = models.CharField(max_length=20, choices=ElectionType.choices)
    period = models.ForeignKey(AcademicPeriod, on_delete=models.PROTECT, related_name="elections")
    faculty = models.ForeignKey(Faculty, on_delete=models.PROTECT, blank=True, null=True, related_name="elections")
    program = models.ForeignKey(Program, on_delete=models.PROTECT, blank=True, null=True, related_name="elections")

    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_elections")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Position(models.Model):
    """Cargo a elegir: presidente de centro, delegado, etc."""
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name="positions")
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    seats = models.PositiveSmallIntegerField(default=1)  # cupos disponibles

    class Meta:
        unique_together = ("election", "name")

    def __str__(self):
        return f"{self.name} ({self.election_id})"


class CandidateList(models.Model):
    """Lista/Frente/Movimiento."""
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name="candidate_lists")
    name = models.CharField(max_length=120)
    acronym = models.CharField(max_length=20, blank=True)
    motto = models.CharField(max_length=255, blank=True)
    logo = models.ImageField(upload_to="lists/logos/", blank=True, null=True)

    class Meta:
        unique_together = ("election", "name")

    def __str__(self):
        return self.name


class Candidacy(models.Model):
    """Postulación de persona a cargo bajo una lista."""
    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name="candidacies")
    candidate_list = models.ForeignKey(CandidateList, on_delete=models.CASCADE, related_name="candidacies")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="candidacies")
    order = models.PositiveSmallIntegerField(default=1)  # orden en lista
    is_principal = models.BooleanField(default=True)

    class Meta:
        unique_together = ("position", "user")
        ordering = ["position", "order"]

    def __str__(self):
        return f"{self.user_id} -> {self.position_id}"


class ElectionRule(models.Model):
    """Reglas configurables por elección."""
    election = models.OneToOneField(Election, on_delete=models.CASCADE, related_name="rules")
    min_turnout_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    allow_blank_vote = models.BooleanField(default=True)
    allow_null_vote = models.BooleanField(default=True)
    max_positions_per_ballot = models.PositiveSmallIntegerField(default=1)
    requires_2fa = models.BooleanField(default=True)

    def __str__(self):
        return f"Rules for election {self.election_id}"