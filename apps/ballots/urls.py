from rest_framework.routers import DefaultRouter
from .views import BallotViewSet, BallotPositionViewSet, BallotOptionViewSet

router = DefaultRouter()
router.register(r"ballots", BallotViewSet, basename="ballot")
router.register(r"ballot-positions", BallotPositionViewSet, basename="ballot-position")
router.register(r"ballot-options", BallotOptionViewSet, basename="ballot-option")

urlpatterns = router.urls