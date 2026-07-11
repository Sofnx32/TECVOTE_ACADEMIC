from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework import status
from django.db.models import Q
from .models import User
from .serializers import UserSerializer


class IsSuperUser(BasePermission):
    """
    Permiso personalizado para asegurar que el usuario 
    esté autenticado y sea estrictamente un SUPERADMIN.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)


class GlobalUsersListView(APIView):
    """
    Lista TODOS los usuarios de TODAS las organizaciones.
    Solo accesible por SUPER ADMIN.
    """
    permission_classes = [IsAuthenticated, IsSuperUser]
    
    def get(self, request):
        # Obtener parámetros de filtro
        organization_id = request.query_params.get('organization', None)
        role = request.query_params.get('role', None)
        is_active = request.query_params.get('is_active', None)
        search = request.query_params.get('search', None)
        
        # Query base
        queryset = User.objects.select_related('organization').all()
        
        # Aplicar filtros
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)
        
        if role:
            queryset = queryset.filter(role=role)
        
        if is_active is not None:
            # Convertir string a booleano
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
        
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) |
                Q(username__icontains=search) |
                Q(institutional_id__icontains=search)
            )
        
        # Ordenar por fecha de creación (más recientes primero)
        queryset = queryset.order_by('-date_joined')
        
        # Serializar
        serializer = UserSerializer(queryset, many=True)
        
        # Estadísticas CORRECTAS
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        inactive_users = User.objects.filter(is_active=False).count()
        
        return Response({
            "users": serializer.data,
            "stats": {
                "total": total_users,
                "active": active_users,
                "inactive": inactive_users,
            }
        })


class GlobalUserDetailView(APIView):
    """
    Ver detalle de un usuario específico.
    Solo accesible por SUPER ADMIN.
    """
    permission_classes = [IsAuthenticated, IsSuperUser]
    
    def get(self, request, user_id):
        try:
            user = User.objects.select_related('organization').get(id=user_id)
            serializer = UserSerializer(user)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response(
                {"error": "Usuario no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )


class GlobalUserToggleActiveView(APIView):
    """
    Activar/Desactivar un usuario.
    Solo accesible por SUPER ADMIN.
    """
    permission_classes = [IsAuthenticated, IsSuperUser]
    
    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            
            # No permitir desactivarse a sí mismo
            if user.id == request.user.id:
                return Response(
                    {"error": "No puedes desactivar tu propio usuario"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user.is_active = not user.is_active
            user.save()
            
            return Response({
                "message": f"Usuario {'activado' if user.is_active else 'desactivado'} correctamente",
                "user_id": str(user.id),
                "is_active": user.is_active
            })
        except User.DoesNotExist:
            return Response(
                {"error": "Usuario no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )