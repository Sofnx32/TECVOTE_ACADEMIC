from django.db import models
from django.conf import settings


class Faculty(models.Model):
    name = models.CharField(max_length=150, unique=True)
    code = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name


class Program(models.Model):
    faculty = models.ForeignKey(Faculty, on_delete=models.PROTECT, related_name="programs")
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=20, unique=True)

    class Meta:
        unique_together = ("faculty", "name")

    def __str__(self):
        return f"{self.name} - {self.faculty.code}"


class AcademicPeriod(models.Model):
    name = models.CharField(max_length=50)  # 2026-I
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class VoterRegistry(models.Model):
    """Padrón electoral académico."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="registries")
    program = models.ForeignKey(Program, on_delete=models.PROTECT, related_name="voter_registries")
    period = models.ForeignKey(AcademicPeriod, on_delete=models.PROTECT, related_name="voter_registries")
    semester = models.PositiveSmallIntegerField()
    is_eligible = models.BooleanField(default=True)
    eligibility_reason = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ("user", "period")

    def __str__(self):
        return f"{self.user_id} - {self.period.name} - elegible={self.is_eligible}"