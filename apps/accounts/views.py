# apps/accounts/views.py

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer, UserSerializer, UserCreateSerializer
from .models import User


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Endpoint de login personalizado.
    Devuelve tokens + datos de usuario + datos de organización.
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]


class UserProfileView(generics.RetrieveAPIView):
    """
    Endpoint para obtener el perfil del usuario autenticado.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class UserListView(generics.ListAPIView):
    """
    Lista todos los usuarios de la organización del usuario autenticado.
    Solo accesible por ADMIN.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Solo ADMIN puede ver la lista de usuarios
        if user.role != "ADMIN":
            return User.objects.none()
        
        # Filtrar por organización
        if user.organization:
            return User.objects.filter(organization=user.organization)
        
        return User.objects.none()


class UserCreateView(generics.CreateAPIView):
    """
    Crear un nuevo usuario en la organización.
    Solo accesible por ADMIN.
    """
    serializer_class = UserCreateSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        user = self.request.user
        
        # Solo ADMIN puede crear usuarios
        if user.role != "ADMIN":
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Solo administradores pueden crear usuarios")
        
        # Asignar la organización del usuario autenticado
        serializer.save(organization=user.organization)