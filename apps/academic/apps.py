# apps/academic/apps.py
from django.apps import AppConfig


class AcademicConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.academic"  # <--- Debe tener el prefijo 'apps.'