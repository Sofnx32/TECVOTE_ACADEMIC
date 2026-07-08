# apps/accounts/urls.py

from django.urls import path
from .views import (
    CustomTokenObtainPairView,
    UserProfileView,
    UserListView,
    UserCreateView,
)

from .global_views import (
    GlobalUsersListView,
    GlobalUserDetailView,
    GlobalUserToggleActiveView,
)

from .two_factor_views import (
    TwoFactorSetupView,
    TwoFactorVerifySetupView,
    TwoFactorLoginView,
    ChangePasswordView,
    TwoFactorStatusView,
    DisableTwoFactorView,
    TwoFactorInitialSetupView,     
    TwoFactorInitialVerifyView,
)


urlpatterns = [
    # Autenticación tradicional
    path("login/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("me/", UserProfileView.as_view(), name="user_profile"),
    
    # Login con 2FA (NUEVO - usar este en el frontend)
    path("login-2fa/", TwoFactorLoginView.as_view(), name="login_2fa"),
    
    # 2FA Setup (requiere JWT - para usuarios ya logueados)
    path("2fa/setup/", TwoFactorSetupView.as_view(), name="2fa_setup"),
    path("2fa/verify/", TwoFactorVerifySetupView.as_view(), name="2fa_verify"),
    path("2fa/status/", TwoFactorStatusView.as_view(), name="2fa_status"),
    path("2fa/disable/", DisableTwoFactorView.as_view(), name="2fa_disable"),
    
    # 2FA Setup INICIAL (SIN JWT - para primer login)
    path("2fa/initial-setup/", TwoFactorInitialSetupView.as_view(), name="2fa_initial_setup"),
    path("2fa/initial-verify/", TwoFactorInitialVerifyView.as_view(), name="2fa_initial_verify"),
    
    # Cambio de contraseña obligatorio
    path("change-password/", ChangePasswordView.as_view(), name="change_password"),
    
    # Gestión de usuarios (Admin de organización)
    path("users/", UserListView.as_view(), name="user_list"),
    path("users/create/", UserCreateView.as_view(), name="user_create"),
    
    # Gestión global de usuarios (Super Admin)
    path("global/users/", GlobalUsersListView.as_view(), name="global_users_list"),
    path("global/users/<int:user_id>/", GlobalUserDetailView.as_view(), name="global_user_detail"),
    path("global/users/<int:user_id>/toggle-active/", GlobalUserToggleActiveView.as_view(), name="global_user_toggle_active"),
]