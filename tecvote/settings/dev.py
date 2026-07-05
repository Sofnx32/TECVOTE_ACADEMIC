import os
from pathlib import Path
from .base import *

# SECURITY
DEBUG = False
SECRET_KEY = config("SECRET_KEY")

# HOSTS
ALLOWED_HOSTS = config("ALLOWED_HOSTS").split(",")

# SECURITY SETTINGS (SSL / HTTPS)
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# HSTS (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = 31536000  # 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# CORS - PRODUCCIÓN
CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS_PROD").split(",")

# EMAIL
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_HOST_USER = config("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = True

# CACHE (Redis para producción)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": config("REDIS_URL", default="redis://127.0.0.1:6379/0"),
    }
}

# LOGGING - CONFIGURACIÓN SEGURA PARA PRODUCCIÓN
# Asegura que la carpeta de logs exista en el servidor para evitar caídas catastróficas
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOGGING["handlers"]["file"] = {
    "class": "logging.handlers.RotatingFileHandler",
    "filename": LOG_DIR / "django.log",
    "maxBytes": 1024 * 1024 * 5,  # 5 MB
    "backupCount": 5,
    "formatter": "verbose",
}

# Combinamos la consola y el archivo para producción
LOGGING["root"]["handlers"] = ["console", "file"]