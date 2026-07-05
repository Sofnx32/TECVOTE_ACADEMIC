from pathlib import Path
from decouple import config
import os

# BASE DIRECTORY
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY
SECRET_KEY = config("SECRET_KEY")  # ❌ Sin default, debe fallar si no existe en el .env
DEBUG = False  # Se sobreescribe en dev.py

# HOSTS
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1").split(",")

# APPLICATION DEFINITION
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Terceros
    "rest_framework",
    "drf_spectacular",
    "corsheaders",

    # Apps locales
    "apps.core",
    "apps.accounts",
    "apps.academic",
    "apps.elections",
    "apps.ballots",
    "apps.voting",
    "apps.results",
    "apps.security",
    "apps.organizations",
]

AUTH_USER_MODEL = "accounts.User"

# MIDDLEWARE - Configurado en orden óptimo para CORS y Seguridad
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",  # ✅ CORREGIDO: Siempre antes de CommonMiddleware
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "tecvote.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "tecvote.wsgi.application"
ASGI_APPLICATION = "tecvote.asgi.application"

# DATABASE
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME", default="tecvote_db"),
        "USER": config("DB_USER", default="postgres"),      
        "PASSWORD": config("DB_PASSWORD"),                  
        "HOST": config("DB_HOST", default="127.0.0.1"),
        "PORT": config("DB_PORT", default="5432"),
    }
}

# PASSWORD VALIDATORS
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# INTERNATIONALIZATION
LANGUAGE_CODE = "es-bo"
TIME_ZONE = "America/La_Paz"
USE_I18N = True
USE_TZ = True

# STATIC FILES
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# DJANGO REST FRAMEWORK (DRF)
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "30/min",
        "user": "120/min",
        "login": "10/min",         # Recuerda asignar throttle_scope = 'login' en tu vista
        "vote_cast": "5/min",       # Recuerda asignar throttle_scope = 'vote_cast' en tu vista
        "receipt_verify": "20/min",  # Recuerda asignar throttle_scope = 'receipt_verify' en tu vista
    },
}

# DRF SPECTACULAR (SWAGGER/OPENAPI)
SPECTACULAR_SETTINGS = {
    "TITLE": "TECVOTE API",
    "DESCRIPTION": "API académica para votaciones",
    "VERSION": "1.0.0",
}

# CORS CONFIGURATION
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:3000,http://127.0.0.1:3000"
).split(",")

# MEDIA FILES
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# LOGGING
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
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": config("DJANGO_LOG_LEVEL", default="INFO"),
            "propagate": False,
        },
    },
}