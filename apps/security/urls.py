from rest_framework.routers import DefaultRouter
from .views import AuditLogViewSet, OneTimeTokenViewSet

router = DefaultRouter()
router.register(r"audit-logs", AuditLogViewSet, basename="audit-log")
router.register(r"one-time-tokens", OneTimeTokenViewSet, basename="one-time-token")

urlpatterns = router.urls