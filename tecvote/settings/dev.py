from .base import *

# Desarrollo local
DEBUG = True

# Hosts permitidos
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

# CORS abierto para desarrollo
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Permisos relajados en desarrollo
REST_FRAMEWORK["DEFAULT_PERMISSION_CLASSES"] = [
    "rest_framework.permissions.AllowAny",
]

# Email en consola (no envía emails reales)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Desactivar SSL en desarrollo
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Sin HSTS en desarrollo
SECURE_HSTS_SECONDS = 0