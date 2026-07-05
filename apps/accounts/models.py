#apps/accounts/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.organizations.models import Organization

class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = "STUDENT", _("Estudiante")
        TEACHER = "TEACHER", _("Docente")
        ADMIN = "ADMIN", _("Administrador")
        ELECTORAL_COMMISSION = "ELECTORAL_COMMISSION", _("Comisión Electoral")
        OBSERVER = "OBSERVER", _("Observador")

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=40, choices=Role.choices, default=Role.STUDENT)
    institutional_id = models.CharField(max_length=30, unique=True)  # matrícula/código institucional
    is_verified = models.BooleanField(default=False)
    organization = models.ForeignKey(Organization,on_delete=models.PROTECT,related_name="users",null=True,blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "institutional_id"]

    def __str__(self):
        return f"{self.email} ({self.role})"