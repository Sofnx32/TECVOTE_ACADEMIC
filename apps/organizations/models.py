# apps/organizations/models.py

import uuid
from django.db import models


class Organization(models.Model):
    class Type(models.TextChoices):
        UNIVERSITY = "UNIVERSITY", "Universidad"
        INSTITUTE = "INSTITUTE", "Instituto"
        SCHOOL = "SCHOOL", "Escuela/Colegio"
        COMPANY = "COMPANY", "Empresa"
        ASSOCIATION = "ASSOCIATION", "Asociación"
        OTHER = "OTHER", "Otro"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # BÁSICO (lo que ya tienes)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=30, unique=True)
    org_type = models.CharField(max_length=20, choices=Type.choices, default=Type.UNIVERSITY)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # BRANDING (AGREGAR AHORA - CRÍTICO PARA TU LOGO)
    logo = models.ImageField(upload_to="organizations/logos/", blank=True, null=True)
    primary_color = models.CharField(max_length=7, default="#0066CC")  # Hex color
    secondary_color = models.CharField(max_length=7, default="#FFD700")  # Hex color
    
    # CONFIGURACIÓN BÁSICA (AGREGAR AHORA)
    country = models.CharField(max_length=100, default="Perú")
    timezone = models.CharField(max_length=50, default="America/Lima")

    def __str__(self):
        return f"{self.name} ({self.code})"
    



class OrganizationRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pendiente"
        APPROVED = "APPROVED", "Aprobada"
        REJECTED = "REJECTED", "Rechazada"
    
    # Datos de la solicitud
    institution_name = models.CharField(max_length=200)
    institution_type = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    estimated_members = models.IntegerField()
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20, blank=True)
    message = models.TextField(blank=True)
    
    # Estado
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    reviewed_by = models.ForeignKey(
        "accounts.User", 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="reviewed_requests"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.institution_name} - {self.status}"