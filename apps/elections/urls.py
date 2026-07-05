from rest_framework.routers import DefaultRouter
from .views import (
    ElectionViewSet,
    PositionViewSet,
    CandidateListViewSet,
    CandidacyViewSet,
    ElectionRuleViewSet,
)

router = DefaultRouter()
router.register(r"elections", ElectionViewSet, basename="election")
router.register(r"positions", PositionViewSet, basename="position")
router.register(r"candidate-lists", CandidateListViewSet, basename="candidate-list")
router.register(r"candidacies", CandidacyViewSet, basename="candidacy")
router.register(r"election-rules", ElectionRuleViewSet, basename="election-rule")

urlpatterns = router.urls