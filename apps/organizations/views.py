# apps/organizations/views.py

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.utils import timezone
import secrets

from .models import Organization, OrganizationRequest
from .serializers import (
    OrganizationSerializer,
    OrganizationRequestSerializer,
    OrganizationRequestDetailSerializer,
)
from apps.accounts.models import User


class OrganizationRequestCreateView(generics.CreateAPIView):
    """
    Endpoint público para solicitar acceso a TECVOTE.
    No requiere autenticación.
    """
    permission_classes = [AllowAny]
    serializer_class = OrganizationRequestSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        organization_request = serializer.save()
        
        # TODO: Enviar email de notificación al superadmin
        
        return Response(
            {
                "message": "Solicitud enviada correctamente. Te contactaremos pronto.",
                "id": str(organization_request.id)
            },
            status=status.HTTP_201_CREATED
        )


class OrganizationRequestListView(generics.ListAPIView):
    """
    Lista todas las solicitudes de organizaciones.
    Solo accesible por SUPER ADMIN.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = OrganizationRequestDetailSerializer
    
    def get_queryset(self):
        # Solo superadmins pueden ver esto
        if not self.request.user.is_superuser:
            return OrganizationRequest.objects.none()
        return OrganizationRequest.objects.all().order_by("-created_at")


class OrganizationRequestApproveView(generics.UpdateAPIView):
    """
    Aprobar una solicitud de organización.
    Solo accesible por SUPER ADMIN.
    """
    permission_classes = [IsAuthenticated]
    queryset = OrganizationRequest.objects.filter(status="PENDING")
    serializer_class = OrganizationRequestDetailSerializer
    
    def update(self, request, *args, **kwargs):
        organization_request = self.get_object()
        
        # Verificar que el usuario es SUPER ADMIN
        if not request.user.is_superuser:
            return Response(
                {"error": "Solo superadministradores pueden aprobar solicitudes"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Crear la organización
        org_code = organization_request.institution_name.lower().replace(" ", "_")[:30]
        organization = Organization.objects.create(
            name=organization_request.institution_name,
            code=org_code,
            org_type=organization_request.institution_type,
            country=organization_request.country,
            is_active=True
        )
        
        # Crear el primer administrador
        temp_password = secrets.token_urlsafe(12)
        admin_user = User.objects.create_user(
            email=organization_request.contact_email,
            username=f"admin_{org_code}",
            password=temp_password,
            role="ADMIN",
            organization=organization,
            is_staff=True
        )
        
        # Actualizar estado de la solicitud
        organization_request.status = "APPROVED"
        organization_request.reviewed_by = request.user
        organization_request.reviewed_at = timezone.now()
        organization_request.save()
        
        # TODO: Enviar email de bienvenida con credenciales
        
        return Response(
            {
                "message": "Solicitud aprobada correctamente",
                "organization": {
                    "id": str(organization.id),
                    "name": organization.name,
                    "code": organization.code
                },
                "admin_user": {
                    "email": admin_user.email,
                    "temp_password": temp_password
                }
            },
            status=status.HTTP_200_OK
        )


class OrganizationRequestRejectView(generics.UpdateAPIView):
    """
    Rechazar una solicitud de organización.
    Solo accesible por SUPER ADMIN.
    """
    permission_classes = [IsAuthenticated]
    queryset = OrganizationRequest.objects.filter(status="PENDING")
    serializer_class = OrganizationRequestDetailSerializer
    
    def update(self, request, *args, **kwargs):
        organization_request = self.get_object()
        
        # Verificar que el usuario es SUPER ADMIN
        if not request.user.is_superuser:
            return Response(
                {"error": "Solo superadministradores pueden rechazar solicitudes"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Obtener razón del rechazo
        rejection_reason = request.data.get("reason", "No proporcionada")
        
        # Actualizar estado
        organization_request.status = "REJECTED"
        organization_request.reviewed_by = request.user
        organization_request.reviewed_at = timezone.now()
        organization_request.rejection_reason = rejection_reason
        organization_request.save()
        
        # TODO: Enviar email de rechazo
        
        return Response(
            {"message": "Solicitud rechazada correctamente"},
            status=status.HTTP_200_OK
        )