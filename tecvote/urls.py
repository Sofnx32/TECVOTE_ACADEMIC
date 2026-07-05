from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

def home(request):
    return JsonResponse({
        "message": "TECVOTE API online",
        "version": "1.0",
        "endpoints": {
            "admin": "/admin/",
            "token": "/api/v1/auth/token/",
            "token_refresh": "/api/v1/auth/token/refresh/",
            "api_docs": "/api/v1/docs/",
            "elections": "/api/v1/elections/",
            "voting": "/api/v1/voting-sessions/",
            "results": "/api/v1/election-results/",
            "verify_receipt": "/api/v1/public/verify-receipt/<code>/"
        }
    })

urlpatterns = [
    path("", home, name="home"),
    path("admin/", admin.site.urls),

    # Autenticación (UNA SOLA VEZ)
    path("api/v1/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/v1/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Apps de la API (CADA UNA UNA SOLA VEZ)
    path("api/v1/", include("apps.elections.urls")),
    path("api/v1/", include("apps.ballots.urls")),
    path("api/v1/", include("apps.voting.urls")),
    path("api/v1/", include("apps.results.urls")),
    path("api/v1/", include("apps.security.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)