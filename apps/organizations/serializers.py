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
            "onboarding_completed",
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


class OrganizationListSerializer(serializers.ModelSerializer):
    """
    Serializer para listar organizaciones en el panel Super Admin.
    """
    members_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "code",
            "org_type",
            "country",
            "is_active",
            "members_count",
            "created_at",
        ]
    
    def get_members_count(self, obj):
        # Contar usuarios de esta organización
        from apps.accounts.models import User
        return User.objects.filter(organization=obj).count()


# ==========================================
# NUEVOS SERIALIZERS PARA DETALLE Y EDICIÓN
# ==========================================

class OrganizationDetailSerializer(serializers.ModelSerializer):
    """
    Serializer detallado para ver toda la info de una organización.
    Incluye conteos de usuarios y formateo de fechas.
    """
    users_count = serializers.SerializerMethodField()
    active_users_count = serializers.SerializerMethodField()
    admins_count = serializers.SerializerMethodField()
    created_at_formatted = serializers.SerializerMethodField()
    org_type_display = serializers.CharField(source="get_org_type_display", read_only=True)

    class Meta:
        model = Organization
        fields = [
            "id", "name", "code", "org_type", "org_type_display",
            "is_active", "created_at", "created_at_formatted",
            "logo", "primary_color", "secondary_color",
            "country", "timezone", "onboarding_completed",
            "users_count", "active_users_count", "admins_count"
        ]

    def get_users_count(self, obj):
        from apps.accounts.models import User
        return User.objects.filter(organization=obj).count()

    def get_active_users_count(self, obj):
        from apps.accounts.models import User
        return User.objects.filter(organization=obj, is_active=True).count()

    def get_admins_count(self, obj):
        from apps.accounts.models import User
        return User.objects.filter(organization=obj, role="ADMIN").count()

    def get_created_at_formatted(self, obj):
        return obj.created_at.strftime("%d/%m/%Y")


class OrganizationUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para editar datos básicos y branding de la organización.
    """
    class Meta:
        model = Organization
        fields = [
            "name", "country", "timezone",
            "primary_color", "secondary_color"
        ]