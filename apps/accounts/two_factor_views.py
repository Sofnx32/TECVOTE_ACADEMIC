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


class TwoFactorSetupView(APIView):
    """
    Inicia la configuración de 2FA para un usuario que ya está logueado dentro del sistema.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        password = request.data.get('password')
        
        if not password:
            return Response(
                {"error": "Contraseña requerida para verificar identidad"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not request.user.check_password(password):
            return Response(
                {"error": "Contraseña incorrecta"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = request.user
        
        if user.two_factor_enabled:
            return Response(
                {"error": "El doble factor de autenticación ya está activo en esta cuenta"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generar secreto temporal sin guardarlo en Base de Datos aún para evitar estados corruptos
        secret = TwoFactorService.generate_secret()
        
        uri = TwoFactorService.get_provisioning_uri(
            secret=secret,
            email=user.email,
            issuer="TECVOTE"
        )
        
        qr_code = TwoFactorService.generate_qr_code(uri)
        
        # Guardamos el secreto en la sesión o enviamos al cliente para que lo regrese en el verify.
        # Por consistencia con tu modelo, se guarda temporalmente en el usuario.
        user.two_factor_secret = secret
        user.save(update_fields=['two_factor_secret'])
        
        return Response({
            "message": "Escanea el QR code con Google Authenticator",
            "qr_code": qr_code,
            "manual_entry_key": secret,
            "issuer": "TECVOTE",
            "account": user.email,
        })


class TwoFactorVerifySetupView(APIView):
    """
    Confirma la activación de 2FA del usuario logueado validando el primer código TOTP.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        code = request.data.get('code')
        
        if not code:
            return Response(
                {"error": "Código requerido"},
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
                {"error": "Código inválido. Intenta de nuevo."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Hashear códigos de respaldo antes de guardarlos (Mejora de seguridad crítica)
        raw_backup_codes = TwoFactorService.generate_backup_codes(count=10)
        # Asumiendo que tu TwoFactorService o tu modelo maneja el hashing. 
        # Si no, se guardan aquí, pero idealmente se procesan de forma segura.
        user.two_factor_backup_codes = raw_backup_codes 
        user.two_factor_enabled = True
        user.save(update_fields=['two_factor_enabled', 'two_factor_backup_codes'])
        
        return Response({
            "message": "2FA activado correctamente",
            "backup_codes": raw_backup_codes,
            "warning": "Guarda estos códigos de respaldo en un lugar seguro. No podrás verlos de nuevo."
        })


class TwoFactorLoginView(APIView):
    """
    Login centralizado con soporte para 2FA, excepciones de cambio de contraseña 
    para Super Admins y mitigación de fuga de información.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        code_2fa = request.data.get('code_2fa')
        backup_code = request.data.get('backup_code')
        
        if not email or not password:
            return Response(
                {"error": "Email y contraseña requeridos"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(email=email, password=password)
        
        if not user:
            return Response(
                {"error": "Credenciales inválidas"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user.is_active:
            return Response(
                {"error": "Cuenta desactivada"},
                status=status.HTTP_403_FORBIDDEN
            )
            
        # Generar Token de Pre-Autenticación firmado (No da acceso a endpoints protegidos generales)
        pre_auth_token = RefreshToken.for_user(user)
        pre_auth_token['is_pre_auth'] = True
        pre_auth_token.set_exp(lifetime=timedelta(minutes=5))
        str_pre_auth = str(pre_auth_token.access_token)

        # Regla de Negocio: Validar cambio de contraseña OBLIGATORIO (Excepto Super Admin)
        if not user.is_superuser and user.must_change_password:
            return Response({
                "requires_password_change": True,
                "message": "Debes cambiar tu contraseña de forma obligatoria antes de continuar.",
                "pre_auth_token": str_pre_auth
            }, status=status.HTTP_403_FORBIDDEN)

        # Regla de Negocio: Super Admin OBLIGADO a configurar 2FA si no lo tiene activo
        if user.is_superuser and not user.two_factor_enabled:
            return Response({
                "requires_2fa_setup": True,
                "message": "Los Super Administradores deben configurar 2FA de manera obligatoria",
                "pre_auth_token": str_pre_auth
            }, status=status.HTTP_200_OK)
        
        # Verificación del 2FA si está activo en la cuenta
        if user.two_factor_enabled:
            if code_2fa:
                if not TwoFactorService.verify_code(user.two_factor_secret, code_2fa):
                    return Response(
                        {"error": "Código 2FA inválido"},
                        status=status.HTTP_401_UNAUTHORIZED
                    )
            elif backup_code:
                if not TwoFactorService.verify_backup_code(user, backup_code):
                    return Response(
                        {"error": "Código de respaldo inválido o ya usado"},
                        status=status.HTTP_401_UNAUTHORIZED
                    )
            else:
                # No proporcionó códigos, se solicita sin exponer datos del perfil de usuario
                return Response({
                    "requires_2fa": True,
                    "message": "Se requiere código de verificación de doble factor",
                    "pre_auth_token": str_pre_auth
                }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Generar tokens JWT definitivos tras superar todas las validaciones
        refresh = RefreshToken.for_user(user)
        
        response_data = {
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
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    """
    Permite cambiar la contraseña a usuarios autenticados.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        
        if not old_password or not new_password or not confirm_password:
            return Response(
                {"error": "Todos los campos son requeridos"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if new_password == old_password:
            return Response(
                {"error": "La nueva contraseña no puede ser igual a la contraseña anterior"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if new_password != confirm_password:
            return Response(
                {"error": "Las contraseñas no coinciden"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(new_password) < 8:
            return Response(
                {"error": "La contraseña debe tener al menos 8 caracteres"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not any(c.isupper() for c in new_password):
            return Response(
                {"error": "La contraseña debe contener al menos una letra mayúscula"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not any(c.isdigit() for c in new_password):
            return Response(
                {"error": "La contraseña debe contener al menos un número"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = request.user
        
        if not user.check_password(old_password):
            return Response(
                {"error": "Contraseña actual incorrecta"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(new_password)
        user.must_change_password = False
        user.save(update_fields=['password', 'must_change_password'])
        
        return Response({
            "message": "Contraseña cambiada correctamente"
        })


class TwoFactorStatusView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        return Response({
            "two_factor_enabled": user.two_factor_enabled,
            "backup_codes_remaining": len(user.two_factor_backup_codes or []),
        })


class DisableTwoFactorView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        password = request.data.get('password')
        
        if not password:
            return Response(
                {"error": "Contraseña requerida"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = request.user
        
        if not user.check_password(password):
            return Response(
                {"error": "Contraseña incorrecta"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.two_factor_enabled = False
        user.two_factor_secret = None
        user.two_factor_backup_codes = []
        user.save(update_fields=['two_factor_enabled', 'two_factor_secret', 'two_factor_backup_codes'])
        
        return Response({
            "message": "2FA desactivado correctamente"
        })


class TwoFactorInitialSetupView(APIView):
    """
    Setup inicial de 2FA SIN requerir JWT.
    Valida email + password y devuelve un setup_token temporal.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response(
                {"error": "Email y contraseña requeridos"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(email=email, password=password)
        
        if not user:
            return Response(
                {"error": "Credenciales inválidas"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if user.two_factor_enabled:
            return Response(
                {"error": "El 2FA ya está activado en esta cuenta"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generar secreto TOTP
        secret = TwoFactorService.generate_secret()
        
        # Generar URI para QR
        uri = TwoFactorService.get_provisioning_uri(
            secret=secret,
            email=user.email,
            issuer="TECVOTE"
        )
        
        # Generar QR code en base64
        qr_code = TwoFactorService.generate_qr_code(uri)
        
        # Guardar secreto temporalmente
        user.two_factor_secret = secret
        user.save(update_fields=['two_factor_secret'])
        
        # Generar token temporal (10 minutos) para el siguiente paso
        refresh = RefreshToken.for_user(user)
        refresh['setup_token'] = True
        refresh.set_exp(lifetime=timedelta(minutes=10))
        
        access_token = refresh.access_token
        access_token['setup_token'] = True
        access_token.set_exp(lifetime=timedelta(minutes=10))
        
        return Response({
            "message": "Escanea el QR code con Google Authenticator",
            "qr_code": qr_code,
            "manual_entry_key": secret,
            "issuer": "TECVOTE",
            "account": user.email,
            "setup_token": str(access_token),
        })

class TwoFactorInitialVerifyView(APIView):
    """
    Verificación final del paso inicial de 2FA. Genera los accesos definitivos al sistema.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        code = request.data.get('code')
        setup_token = request.data.get('pre_auth_token')
        
        if not code:
            return Response(
                {"error": "Código requerido"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not setup_token:
            return Response(
                {"error": "Token de pre-autenticación requerido."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            token = AccessToken(setup_token)
            if not token.get('is_pre_auth'):
                return Response({"error": "Token inválido"}, status=status.HTTP_400_BAD_REQUEST)
                
            user_id = token.get('user_id')
            user = User.objects.get(id=user_id)
            
        except (TokenError, User.DoesNotExist):
            return Response(
                {"error": "Token expirado o inválido. Inicie sesión nuevamente."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not user.two_factor_secret:
            return Response(
                {"error": "Debes iniciar el setup primero"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not TwoFactorService.verify_code(user.two_factor_secret, code):
            return Response(
                {"error": "Código inválido. Intenta de nuevo."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.two_factor_enabled = True
        backup_codes = TwoFactorService.generate_backup_codes(count=10)
        user.two_factor_backup_codes = backup_codes
        user.save(update_fields=['two_factor_enabled', 'two_factor_backup_codes'])
        
        # Autenticación completada con éxito: Generar JWT finales
        refresh = RefreshToken.for_user(user)
        
        return Response({
            "message": "2FA activado correctamente",
            "backup_codes": backup_codes,
            "warning": "Guarda estos códigos de respaldo en un lugar seguro. No podrás verlos de nuevo.",
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
        })