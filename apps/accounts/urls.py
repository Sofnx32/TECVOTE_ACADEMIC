# apps/accounts/urls.py

from django.urls import path
from .views import (
    CustomTokenObtainPairView,
    UserProfileView,
    UserListView,
    UserCreateView,
)

urlpatterns = [
    # Login personalizado (con branding dinámico)
    path("login/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    
    # Perfil del usuario autenticado
    path("me/", UserProfileView.as_view(), name="user_profile"),
    
    # Gestión de usuarios (solo ADMIN)
    path("users/", UserListView.as_view(), name="user_list"),
    path("users/create/", UserCreateView.as_view(), name="user_create"),
]