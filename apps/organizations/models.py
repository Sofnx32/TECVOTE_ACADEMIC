import uuid
from django.db import models


class Organization(models.Model):
    class Type(models.TextChoices):
        UNIVERSITY = "UNIVERSITY", "University"
        INSTITUTE = "INSTITUTE", "Institute"
        SCHOOL = "SCHOOL", "School"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=30, unique=True)
    org_type = models.CharField(max_length=20, choices=Type.choices)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.code})"