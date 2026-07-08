from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import timedelta
from .models import Organization, OrganizationRequest
from apps.accounts.models import User


class GlobalStatsView(APIView):
    """
    Estadísticas globales para el Dashboard del Super Admin.
    Solo accesible por SUPER ADMIN.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Verificar que es superadmin
        if not request.user.is_superuser:
            return Response({"error": "No autorizado"}, status=403)
        
        # Estadísticas básicas
        total_organizations = Organization.objects.count()
        active_organizations = Organization.objects.filter(is_active=True).count()
        total_users = User.objects.count()
        pending_requests = OrganizationRequest.objects.filter(status="PENDING").count()
        
        # TODO: Cuando tengamos elecciones, agregar:
        # total_elections = Election.objects.count()
        total_elections = 0  # Placeholder
        
        # TODO: Cuando tengamos pagos, agregar:
        # monthly_revenue = Subscription.objects.filter(...).aggregate(Sum('amount'))
        monthly_revenue = 125000  # Placeholder
        
        # Organizaciones por tipo
        orgs_by_type = (
            Organization.objects.values('org_type')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        
        # Organizaciones por país
        orgs_by_country = (
            Organization.objects.values('country')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]  # Top 10 países
        )
        
        # Crecimiento mensual (últimos 6 meses)
        today = timezone.now()
        monthly_growth = []
        for i in range(5, -1, -1):
            month_date = today - timedelta(days=i*30)
            month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_end = (month_start + timedelta(days=32)).replace(day=1)
            
            count = Organization.objects.filter(
                created_at__gte=month_start,
                created_at__lt=month_end
            ).count()
            
            monthly_growth.append({
                "month": month_start.strftime("%b %Y"),
                "count": count
            })
        
        # Solicitudes recientes (últimas 5)
        recent_requests = (
            OrganizationRequest.objects
            .filter(status="PENDING")
            .order_by("-created_at")[:5]
            .values(
                "id",
                "institution_name",
                "institution_type",
                "country",
                "contact_email",
                "estimated_members",
                "created_at"
            )
        )
        
        # Organizaciones recientes (últimas 5)
        recent_organizations = (
            Organization.objects
            .order_by("-created_at")[:5]
            .values(
                "id",
                "name",
                "org_type",
                "country",
                "is_active",
                "created_at"
            )
        )
        
        # Agregar conteo de miembros a cada organización
        for org in recent_organizations:
            org["members"] = User.objects.filter(organization_id=org["id"]).count()
        
        return Response({
            "stats": {
                "totalOrganizations": total_organizations,
                "activeOrganizations": active_organizations,
                "totalUsers": total_users,
                "totalElections": total_elections,
                "monthlyRevenue": monthly_revenue,
                "pendingRequests": pending_requests,
            },
            "orgsByType": list(orgs_by_type),
            "orgsByCountry": list(orgs_by_country),
            "monthlyGrowth": monthly_growth,
            "recentRequests": list(recent_requests),
            "recentOrganizations": list(recent_organizations),
        })