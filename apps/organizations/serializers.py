# apps/organizations/serializers.py

from rest_framework import serializers
from .models import Organization, OrganizationRequest


class OrganizationSerializer(serializers.ModelSerializer):
    """
    Serializer para mostrar datos de la organización.
    Se usa en el login para devolver branding dinámico.
    """
    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "code",
            "org_type",
            "logo",
            "primary_color",
            "secondary_color",
            "country",
            "timezone",
            "is_active",
        ]
        read_only_fields = ["id", "code"]


class OrganizationRequestSerializer(serializers.ModelSerializer):
    """
    Serializer para crear solicitudes de nuevas organizaciones.
    Es público (no requiere autenticación).
    """
    class Meta:
        model = OrganizationRequest
        fields = [
            "id",
            "institution_name",
            "institution_type",
            "country",
            "estimated_members",
            "contact_email",
            "contact_phone",
            "message",
            "status",
            "created_at",
        ]
        read_only_fields = ["id", "status", "created_at"]
    
    def validate_estimated_members(self, value):
        if value <= 0:
            raise serializers.ValidationError("El número de miembros debe ser mayor a 0")
        return value
    
    def validate_contact_email(self, value):
        # Verificar que no haya una solicitud pendiente con el mismo email
        if OrganizationRequest.objects.filter(
            contact_email=value, 
            status="PENDING"
        ).exists():
            raise serializers.ValidationError(
                "Ya existe una solicitud pendiente con este email"
            )
        return value


class OrganizationRequestDetailSerializer(serializers.ModelSerializer):
    """
    Serializer detallado para el SUPER ADMIN.
    Incluye todos los campos para revisión.
    """
    class Meta:
        model = OrganizationRequest
        fields = "__all__"
        read_only_fields = [
            "id",
            "institution_name",
            "institution_type",
            "country",
            "estimated_members",
            "contact_email",
            "contact_phone",
            "message",
            "status",
            "reviewed_by",
            "reviewed_at",
            "rejection_reason",
            "created_at",
            "updated_at",
        ]