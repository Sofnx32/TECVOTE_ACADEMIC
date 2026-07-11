from rest_framework import permissions
import logging

logger = logging.getLogger(__name__)

class IsElectionManagerOrReadOnly(permissions.BasePermission):
    """
    Permite lectura a cualquier usuario autenticado, 
    pero solo ciertos roles pueden modificar/crear.
    """
    
    def has_permission(self, request, view):
        user = request.user
        
        logger.info(f"[PERMISSION] User: {user.email if user.is_authenticated else 'Anonymous'} | Method: {request.method} | is_superuser: {user.is_superuser}")
        
        if not user.is_authenticated:
            logger.warning("[PERMISSION] Usuario no autenticado")
            return False

        if request.method in permissions.SAFE_METHODS:
            logger.info("[PERMISSION] Método SAFE (GET) → Permitido")
            return True

        # Para POST, PUT, DELETE
        is_allowed = (
            user.is_superuser or 
            getattr(user, 'is_election_manager', False) or
            getattr(user, 'role', None) in ['SUPER_ADMIN', 'ADMIN']
        )

        if is_allowed:
            logger.info(f"[PERMISSION] Usuario {user.email} tiene permisos de escritura")
        else:
            logger.warning(f"[PERMISSION] Usuario {user.email} NO tiene permisos de escritura")

        return is_allowed