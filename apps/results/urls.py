from rest_framework.routers import DefaultRouter
from .views import TallyViewSet, ElectionResultViewSet, ElectionLifecycleViewSet

router = DefaultRouter()
router.register(r"tallies", TallyViewSet, basename="tally")
router.register(r"election-results", ElectionResultViewSet, basename="election-result")
router.register(r"election-lifecycle", ElectionLifecycleViewSet, basename="election-lifecycle")

urlpatterns = router.urls