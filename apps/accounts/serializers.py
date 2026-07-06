# apps/accounts/serializers.py

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from .models import User
from apps.organizations.serializers import OrganizationSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer personalizado que devuelve:
    - Tokens JWT (access, refresh)
    - Datos del usuario
    - Datos de la organización (para branding dinámico)
    """
    
    def validate(self, attrs):
        # Autenticar usuario
        user = authenticate(
            email=attrs.get("email"),
            password=attrs.get("password")
        )
        
        if not user:
            raise serializers.ValidationError("Credenciales inválidas")
        
        if not user.is_active:
            raise serializers.ValidationError("Cuenta desactivada")
        
        # Verificar que la organización esté activa
        if user.organization and not user.organization.is_active:
            raise serializers.ValidationError("La organización está desactivada")
        
        # Generar tokens
        data = {}
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        data["refresh"] = str(refresh)
        data["access"] = str(refresh.access_token)
        
        # Agregar datos del usuario
        data["user"] = {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "role": user.role,
            "institutional_id": user.institutional_id,
            "is_verified": user.is_verified,
            "is_superuser": user.is_superuser,  
        }
        
        # Agregar datos de la organización (para branding dinámico)
        if user.organization:
            data["organization"] = OrganizationSerializer(user.organization).data
        else:
            data["organization"] = None
        
        return data


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer para mostrar datos del usuario.
    """
    organization = OrganizationSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "role",
            "institutional_id",
            "is_verified",
            "organization",
        ]
        read_only_fields = ["id", "email"]


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear usuarios.
    Solo accesible por ADMIN de la organización.
    """
    password = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = [
            "email",
            "username",
            "password",
            "role",
            "institutional_id",
            "organization",
        ]
    
    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user