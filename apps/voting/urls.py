from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import VotingSessionViewSet, VoteViewSet, VoteSelectionViewSet
from .public_verification_views import ReceiptVerificationView

router = DefaultRouter()
router.register(r"voting-sessions", VotingSessionViewSet, basename="voting-session")
router.register(r"votes", VoteViewSet, basename="vote")
router.register(r"vote-selections", VoteSelectionViewSet, basename="vote-selection")


urlpatterns = [
    path("public/verify-receipt/<str:receipt_code>/", ReceiptVerificationView.as_view(), name="verify-receipt"),
] + router.urls