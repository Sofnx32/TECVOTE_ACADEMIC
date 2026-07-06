# apps/organizations/urls.py

from django.urls import path
from .views import (
    OrganizationRequestCreateView,
    OrganizationRequestListView,
    OrganizationRequestApproveView,
    OrganizationRequestRejectView,
)

urlpatterns = [
    # Público: Crear solicitud
    path("requests/", OrganizationRequestCreateView.as_view(), name="organization-request-create"),
    
    # SUPER ADMIN: Listar solicitudes
    path("requests/list/", OrganizationRequestListView.as_view(), name="organization-request-list"),
    
    # SUPER ADMIN: Aprobar solicitud
    path("requests/<uuid:pk>/approve/", OrganizationRequestApproveView.as_view(), name="organization-request-approve"),
    
    # SUPER ADMIN: Rechazar solicitud
    path("requests/<uuid:pk>/reject/", OrganizationRequestRejectView.as_view(), name="organization-request-reject"),
]