import logging
from datetime import timedelta
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from .models import User
from .serializers import UserSerializer
from .two_factor_service import TwoFactorService
from apps.organizations.serializers import OrganizationSerializer

logger = logging.getLogger(__name__)

class TwoFactorSetupView(APIView):
    """
    Inicia la configuracion de 2FA para un usuario autenticado dentro del sistema.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        password = request.data.get('password')
        
        if not password:
            return Response(
                {"error": "Contrasena requerida para verificar identidad"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not request.user.check_password(password):
            return Response(
                {"error": "Contrasena incorrecta"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = request.user
        
        if user.two_factor_enabled:
            return Response(
                {"error": "El doble factor de autenticacion ya esta activo en esta cuenta"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        secret = TwoFactorService.generate_secret()
        
        uri = TwoFactorService.get_provisioning_uri(
            secret=secret,
            email=user.email,
            issuer="TECVOTE"
        )
        
        qr_code = TwoFactorService.generate_qr_code(uri)
        user.two_factor_secret = secret
        user.save(update_fields=['two_factor_secret'])
        
        return Response({
            "message": "Escanea el QR code con Google Authenticator",
            "qr_code": qr_code,
            "manual_entry_key": secret,
            "issuer": "TECVOTE",
            "account": user.email,
        }, status=status.HTTP_200_OK)


class TwoFactorVerifySetupView(APIView):
    """
    Confirma la activacion de 2FA validando el primer codigo TOTP.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        code = request.data.get('code')
        
        if not code:
            return Response(
                {"error": "Codigo requerido"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = request.user
        
        if not user.two_factor_secret:
            return Response(
                {"error": "Debes iniciar el setup primero"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not TwoFactorService.verify_code(user.two_factor_secret, code):
            return Response(
                {"error": "Codigo invalido. Intenta de nuevo."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        raw_backup_codes = TwoFactorService.generate_backup_codes(count=10)
        user.two_factor_backup_codes = raw_backup_codes 
        user.two_factor_enabled = True
        user.save(update_fields=['two_factor_enabled', 'two_factor_backup_codes'])
        
        return Response({
            "message": "2FA activado correctamente",
            "backup_codes": raw_backup_codes,
            "warning": "Guarda estos codigos de respaldo en un lugar seguro. No podras verlos de nuevo."
        }, status=status.HTTP_200_OK)


class TwoFactorLoginView(APIView):
    """
    Login centralizado con soporte estricto de 2FA y manejo jerárquico de 
    cambio de contraseña obligatorio tanto para Admins como Superusuarios.
    """
    permission_classes = [AllowAny]
    authentication_classes = () 
    
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        code_2fa = request.data.get('code_2fa')
        backup_code = request.data.get('backup_code')
        
        if not email or not password:
            return Response(
                {"error": "Email y contrasena requeridos"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(email=email, password=password)
        
        if not user:
            return Response(
                {"error": "Credenciales invalidas"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user.is_active:
            return Response(
                {"error": "Cuenta desactivada"},
                status=status.HTTP_403_FORBIDDEN
            )
            
        # Generación del token temporal reutilizable para los flujos intermedios
        pre_auth_token = RefreshToken.for_user(user)
        pre_auth_token['is_pre_auth'] = True
        pre_auth_token.set_exp(lifetime=timedelta(minutes=5))
        str_pre_auth = str(pre_auth_token.access_token)

        if not user.two_factor_enabled:
            return Response({
                "requires_2fa_setup": True,
                "message": "Debe configurar el doble factor de autenticación (2FA) de manera obligatoria",
                "pre_auth_token": str_pre_auth
            }, status=status.HTTP_200_OK)
        
        # ⚡ PASO 2: Si tiene el 2FA activo, se exige y valida el código de verificación
        if user.two_factor_enabled:
            if code_2fa:
                if not TwoFactorService.verify_code(user.two_factor_secret, code_2fa):
                    return Response(
                        {"error": "Codigo 2FA invalido"},
                        status=status.HTTP_401_UNAUTHORIZED
                    )
            elif backup_code:
                if not TwoFactorService.verify_backup_code(user, backup_code):
                    return Response(
                        {"error": "Codigo de respaldo invalido o ya usado"},
                        status=status.HTTP_401_UNAUTHORIZED
                    )
            else:
                return Response({
                    "requires_2fa": True,
                    "message": "Se requiere codigo de verificacion de doble factor",
                    "pre_auth_token": str_pre_auth
                }, status=status.HTTP_200_OK)
        
        if user.must_change_password:
            return Response({
                "requires_password_change": True,
                "message": "Debes cambiar tu contrasena de forma obligatoria antes de continuar.",
                "pre_auth_token": str_pre_auth 
            }, status=status.HTTP_200_OK)
        
        # ⚡ PASO 4: Autenticación exitosa y emisión de credenciales finales
        refresh = RefreshToken.for_user(user)
        
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "role": user.role,
                "institutional_id": user.institutional_id,
                "is_verified": user.is_verified,
                "is_superuser": user.is_superuser,
                "two_factor_enabled": user.two_factor_enabled,
            },
            "organization": OrganizationSerializer(user.organization).data if user.organization else None,
        }, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    """
    Permite cambiar la contrasena validando de forma segura tokens de acceso y pre-autenticación.
    """
    permission_classes = [AllowAny]
    authentication_classes = ()

    def post(self, request):
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        
        auth_header = request.headers.get('Authorization', '')
        setup_token = None
        
        if auth_header:
            parts = auth_header.split(' ')
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                setup_token = parts[1]
            else:
                setup_token = parts[0]
        else:
            setup_token = request.data.get('pre_auth_token')

        if not old_password or not new_password or not confirm_password:
            return Response(
                {"error": "Todos los campos son requeridos"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not setup_token:
            return Response(
                {"error": "Token de autenticación requerido para cambiar contraseña"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            token = AccessToken(setup_token)
            user_id = token.get('user_id')
            user = User.objects.get(id=user_id)
        except Exception as e:
            return Response(
                {"error": f"Token inválido o expirado: {str(e)}"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if new_password == old_password:
            return Response(
                {"error": "La nueva contrasena no puede ser igual a la contrasena anterior"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if new_password != confirm_password:
            return Response(
                {"error": "Las contrasenas no coinciden"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(new_password) < 8:
            return Response(
                {"error": "La contrasena debe tener al menos 8 caracteres"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not any(c.isupper() for c in new_password):
            return Response(
                {"error": "La contrasena debe contener al menos una letra mayuscula"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not any(c.isdigit() for c in new_password):
            return Response(
                {"error": "La contrasena debe contener al menos un numero"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not user.check_password(old_password):
            return Response(
                {"error": "Contrasena actual incorrecta"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.must_change_password = False
        user.save()

        refresh = RefreshToken.for_user(user)

        return Response({
            "message": "Contrasena cambiada correctamente",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "role": user.role,
                "institutional_id": user.institutional_id,
                "is_verified": user.is_verified,
                "is_superuser": user.is_superuser,
                "two_factor_enabled": user.two_factor_enabled,
            },
            "organization": OrganizationSerializer(user.organization).data if user.organization else None,
        }, status=status.HTTP_200_OK)


class TwoFactorStatusView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        return Response({
            "two_factor_enabled": user.two_factor_enabled,
            "backup_codes_remaining": len(user.two_factor_backup_codes or []),
        }, status=status.HTTP_200_OK)


class DisableTwoFactorView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        password = request.data.get('password')
        
        if not password:
            return Response(
                {"error": "Contrasena requerida"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = request.user
        
        if not user.check_password(password):
            return Response(
                {"error": "Contrasena incorrecta"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.two_factor_enabled = False
        user.two_factor_secret = None
        user.two_factor_backup_codes = []
        user.save(update_fields=['two_factor_enabled', 'two_factor_secret', 'two_factor_backup_codes'])
        
        return Response({
            "message": "2FA desactivado correctamente"
        }, status=status.HTTP_200_OK)


class TwoFactorInitialSetupView(APIView):
    """
    Setup inicial de 2FA sin requerir JWT persistente en cabecera.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response(
                {"error": "Email y contrasena son requeridos"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(email=email, password=password)
        
        if not user:
            return Response(
                {"error": "Credenciales invalidas"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if user.two_factor_enabled:
            return Response(
                {"error": "El 2FA ya esta activo en esta cuenta"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        secret = TwoFactorService.generate_secret()
        user.two_factor_secret = secret
        user.save(update_fields=['two_factor_secret'])
        
        uri = TwoFactorService.get_provisioning_uri(
            secret=secret,
            email=user.email,
            issuer="TECVOTE"
        )
        qr_code = TwoFactorService.generate_qr_code(uri)
        
        refresh = RefreshToken.for_user(user)
        refresh['is_pre_auth'] = True  
        refresh.set_exp(lifetime=timedelta(minutes=10))
        
        access_token = refresh.access_token
        access_token['is_pre_auth'] = True  
        access_token.set_exp(lifetime=timedelta(minutes=10))
        
        return Response({
            "message": "Escanea el QR code con Google Authenticator",
            "qr_code": qr_code,
            "manual_entry_key": secret,
            "issuer": "TECVOTE",
            "account": user.email,
            "pre_auth_token": str(access_token),  
        }, status=status.HTTP_200_OK)
    
    
class TwoFactorInitialVerifyView(APIView):
    """
    Valida el código del setup inicial y verifica si el usuario debe pasar al cambio de contraseña obligatoria.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        code = request.data.get('code')
        setup_token = request.data.get('pre_auth_token') or request.data.get('setup_token')
        
        if not code:
            return Response({"error": "Codigo de 6 digitos requerido"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not setup_token:
            return Response({"error": "Token de pre-autenticacion requerido"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            token = AccessToken(setup_token)
            if not token.get('is_pre_auth'):
                return Response({"error": "Token invalido para esta operacion (no es pre-auth)"}, status=status.HTTP_400_BAD_REQUEST)
                
            user_id = token.get('user_id')
            user = User.objects.get(id=user_id)
        except TokenError as e:
            return Response({"error": f"Token invalido o expirado: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not user.two_factor_secret:
            return Response({"error": "Debes iniciar el setup primero (no hay secret)"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not TwoFactorService.verify_code(user.two_factor_secret, code):
            return Response({
                "error": "Codigo de verifcacion incorrecto. Verifique su aplicación Google Authenticator."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user.two_factor_enabled = True
        backup_codes = TwoFactorService.generate_backup_codes(count=10)
        user.two_factor_backup_codes = backup_codes
        user.save(update_fields=['two_factor_enabled', 'two_factor_backup_codes'])
        
        if user.must_change_password:
            refresh = RefreshToken.for_user(user)
            refresh['is_pre_auth'] = True
            refresh.set_exp(lifetime=timedelta(minutes=5))
            return Response({
                "requires_password_change": True,
                "message": "2FA activado. Ahora debes cambiar tu contrasena de forma obligatoria.",
                "pre_auth_token": str(refresh.access_token)
            }, status=status.HTTP_200_OK)
            
        refresh = RefreshToken.for_user(user)
        
        return Response({
            "message": "2FA activado correctamente",
            "backup_codes": backup_codes,
            "warning": "Guarda estos codigos de respaldo en un lugar seguro. No podras verlos de nuevo.",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "role": user.role,
                "institutional_id": user.institutional_id,
                "is_verified": user.is_verified,
                "is_superuser": user.is_superuser,
                "two_factor_enabled": user.two_factor_enabled,
            },
            "organization": OrganizationSerializer(user.organization).data if user.organization else None,
        }, status=status.HTTP_200_OK)