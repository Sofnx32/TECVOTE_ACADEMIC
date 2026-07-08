from django.urls import path
from .views import (
    OrganizationRequestCreateView,
    OrganizationRequestListView,
    OrganizationRequestApproveView,
    OrganizationRequestRejectView,
    OrganizationListView,
    OrganizationDetailView,  # ← AGREGAR
    OrganizationUpdateView,  # ← AGREGAR
    OrganizationToggleActiveView,  # ← AGREGAR
    OrganizationStatsView,  # ← AGREGAR
    OrganizationCompleteOnboardingView,
    OrganizationUpdateBrandingView,
)
from .stats_views import GlobalStatsView

urlpatterns = [
    # Estadísticas globales (debe ir ANTES de <uuid:pk>)
    path("stats/", GlobalStatsView.as_view(), name="organization-stats"),
    
    # Onboarding y Branding (deben ir ANTES de <uuid:pk>)
    path("complete-onboarding/", OrganizationCompleteOnboardingView.as_view(), name="complete-onboarding"),
    path("update-branding/", OrganizationUpdateBrandingView.as_view(), name="organization-update-branding"),
    
    # Lista y solicitudes
    path("", OrganizationListView.as_view(), name="organization-list"),
    path("requests/", OrganizationRequestCreateView.as_view(), name="organization-request-create"),
    path("requests/list/", OrganizationRequestListView.as_view(), name="organization-request-list"),
    
    # Acciones de requests (usan <int:pk>)
    path("requests/<int:pk>/approve/", OrganizationRequestApproveView.as_view(), name="organization-request-approve"),
    path("requests/<int:pk>/reject/", OrganizationRequestRejectView.as_view(), name="organization-request-reject"),
    
    # DEBEN IR AL FINAL
    path("<uuid:pk>/", OrganizationDetailView.as_view(), name="organization-detail"),
    path("<uuid:pk>/update/", OrganizationUpdateView.as_view(), name="organization-update"),
    path("<uuid:pk>/toggle-active/", OrganizationToggleActiveView.as_view(), name="organization-toggle-active"),
    path("<uuid:pk>/stats/", OrganizationStatsView.as_view(), name="organization-stats-detail"),
]