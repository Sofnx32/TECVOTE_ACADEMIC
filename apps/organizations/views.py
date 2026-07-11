from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.utils import timezone
from django.db.models import Count
from django.shortcuts import get_object_or_404
import secrets
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser

from .models import Organization, OrganizationRequest
from .serializers import (
    OrganizationSerializer,
    OrganizationRequestSerializer,
    OrganizationRequestDetailSerializer,
    OrganizationListSerializer,
    OrganizationDetailSerializer,
    OrganizationUpdateSerializer,
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
        
        # 1. Verificar permisos
        if not request.user.is_superuser:
            return Response(
                {"error": "Solo superadministradores pueden aprobar solicitudes"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 2. Generar código único para la organización
        base_code = organization_request.institution_name.lower().replace(" ", "_")[:20]
        org_code = base_code
        counter = 1
        while Organization.objects.filter(code=org_code).exists():
            org_code = f"{base_code}_{counter}"
            counter += 1
        
        # 3. Verificar que el email no exista ya
        if User.objects.filter(email=organization_request.contact_email).exists():
            return Response(
                {"error": f"El email {organization_request.contact_email} ya está registrado."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 4. Crear la Organización
        organization = Organization.objects.create(
            name=organization_request.institution_name,
            code=org_code,
            org_type=organization_request.institution_type,
            country=organization_request.country,
            is_active=True,
            # Valores por defecto para branding
            primary_color="#0066CC",
            secondary_color="#FFD700",
        )
        
        # 5. Generar credenciales seguras
        temp_password = secrets.token_urlsafe(12)
        institutional_id = f"ADMIN-{org_code.upper()}"
        
        # Generar username único
        base_username = f"admin_{org_code}"
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1
        
        # 6. Crear el Usuario ADMIN
        admin_user = User.objects.create_user(
            email=organization_request.contact_email,
            username=username,
            password=temp_password,
            role="ADMIN",
            institutional_id=institutional_id,
            organization=organization,
            is_staff=True,
            is_verified=True,
        )
        
        # 7. Actualizar la solicitud
        organization_request.status = "APPROVED"
        organization_request.reviewed_by = request.user
        organization_request.reviewed_at = timezone.now()
        organization_request.save()
        
        # 8. Devolver credenciales al Super Admin
        return Response(
            {
                "message": "Solicitud aprobada y usuario creado exitosamente.",
                "organization": {
                    "id": str(organization.id),
                    "name": organization.name,
                    "code": organization.code,
                },
                "admin_user": {
                    "email": admin_user.email,
                    "username": admin_user.username,
                    "institutional_id": admin_user.institutional_id,
                    "temp_password": temp_password,
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


class OrganizationListView(generics.ListAPIView):
    """
    Lista todas las organizaciones activas.
    Solo accesible por SUPER ADMIN.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = OrganizationListSerializer
    
    def get_queryset(self):
        if not self.request.user.is_superuser:
            return Organization.objects.none()
        return Organization.objects.all().order_by("-created_at")


class OrganizationDetailView(generics.RetrieveAPIView):
    """
    Ver detalle completo de una organización.
    Solo Super Admin.
    """
    permission_classes = [IsAuthenticated]
    queryset = Organization.objects.all()
    serializer_class = OrganizationDetailSerializer
    lookup_field = "pk"


class OrganizationUpdateView(generics.UpdateAPIView):
    """
    Actualizar información y branding.
    Solo Super Admin.
    """
    permission_classes = [IsAuthenticated]
    queryset = Organization.objects.all()
    serializer_class = OrganizationUpdateSerializer
    lookup_field = "pk"


class OrganizationToggleActiveView(APIView):
    """
    Activar/Desactivar organización.
    Solo Super Admin.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        if not request.user.is_superuser:
            return Response({"error": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)
        
        org = get_object_or_404(Organization, pk=pk)
        org.is_active = not org.is_active
        org.save()
        
        return Response({
            "message": f"Organización {'activada' if org.is_active else 'desactivada'} correctamente",
            "is_active": org.is_active
        })


class OrganizationStatsView(APIView):
    """
    Estadísticas específicas de una organización.
    Solo Super Admin.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        if not request.user.is_superuser:
            return Response({"error": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)
        
        org = get_object_or_404(Organization, pk=pk)
        
        # Usuarios por rol
        users_by_role = (
            User.objects.filter(organization=org)
            .values('role')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        
        total_users = User.objects.filter(organization=org).count()
        active_users = User.objects.filter(organization=org, is_active=True).count()
        
        # TODO: Cuando tengamos elecciones, descomentar:
        # elections_count = Election.objects.filter(organization=org).count()
        # active_elections = Election.objects.filter(organization=org, status='ACTIVE').count()
        elections_count = 0
        active_elections = 0
        
        return Response({
            "total_users": total_users,
            "active_users": active_users,
            "users_by_role": list(users_by_role),
            "elections_count": elections_count,
            "active_elections": active_elections,
        })


class OrganizationCompleteOnboardingView(APIView):
    """
    Marcar onboarding como completado.
    Solo accesible por ADMIN de la organización.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        org = request.user.organization
        
        if not org:
            return Response(
                {"error": "Usuario sin organización"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        org.onboarding_completed = True
        org.onboarding_completed_at = timezone.now()
        org.save()
        
        return Response({
            "message": "Onboarding completado exitosamente",
            "organization": OrganizationSerializer(org).data
        })


class OrganizationUpdateBrandingView(APIView):
    """
    Actualizar branding de la organización (logo, colores, código).
    Solo accesible por ADMIN de la organización.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def patch(self, request):
        org = request.user.organization
        
        if not org:
            return Response(
                {"error": "Usuario sin organización"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # SOLUCIÓN DEFINITIVA AL 403: Normaliza el rol a mayúsculas y quita espacios
        user_role = getattr(request.user, 'role', '')
        if str(user_role).upper().strip() != "ADMIN":
            return Response(
                {"error": f"Solo administradores pueden actualizar el branding. Tu rol detectado es: {user_role}"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Actualizar campos si existen en la petición
        if 'name' in request.data:
            org.name = request.data['name']
        
        if 'code' in request.data:
            if Organization.objects.filter(code=request.data['code']).exclude(id=org.id).exists():
                return Response(
                    {"error": "Este código ya está en uso"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            org.code = request.data['code']
        
        if 'primary_color' in request.data:
            org.primary_color = request.data['primary_color']
        
        if 'secondary_color' in request.data:
            org.secondary_color = request.data['secondary_color']
        
        if 'logo' in request.data:
            org.logo = request.data['logo']
        
        org.save()
        
        return Response({
            "message": "Branding actualizado correctamente",
            "organization": OrganizationSerializer(org).data
        })