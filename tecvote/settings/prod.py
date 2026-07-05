from .base import *
from decouple import config  # ✅ Añadido: Necesario para usar config()
import dj_database_url

DEBUG = False

# SECRET_KEY para producción
SECRET_KEY = config("SECRET_KEY")

# ALLOWED_HOSTS desde variable de entorno
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default=".onrender.com").split(",")

# DATABASE - Render provee la variable DATABASE_URL automáticamente
DATABASES = {
    "default": dj_database_url.config(
        default=config("DATABASE_URL", default=None),
        conn_max_age=600,
        ssl_require=True  # Render exige SSL para conectar a la base de datos
    )
}

# SECURITY & SSL
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000  # 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# ✅ CRÍTICO PARA RENDER: Evita bucles infinitos de redirección HTTPS
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# CORS
CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS_PROD", default="").split(",")

# STATIC FILES & WHITENOISE
STATIC_ROOT = BASE_DIR / "staticfiles"

# ✅ CORREGIDO: Formato moderno de almacenamiento para Django 5.x (WhiteNoise)
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# ✅ Inyección dinámica del Middleware de WhiteNoise en la posición correcta
if "whitenoise.middleware.WhiteNoiseMiddleware" not in MIDDLEWARE:
    # Debe ir inmediatamente después de SecurityMiddleware
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

# LOGGING - Optimizado para los flujos de lectura de Render
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

