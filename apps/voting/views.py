from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import VotingSession, Vote, VoteSelection
from .serializers import (
    VotingSessionSerializer,
    VoteSerializer,
    VoteSelectionSerializer,
    CastVoteSerializer,
)
from .services import cast_vote


class VotingSessionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = VotingSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return VotingSession.objects.select_related("election", "voter").filter(voter=self.request.user)


class VoteViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = VoteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Vote.objects.select_related("election", "voter", "session").filter(voter=self.request.user)


    @action(detail=False, methods=["post"], url_path="cast")
    def cast(self, request):
        serializer = CastVoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        vote = cast_vote(
            user=request.user,
            election_id=serializer.validated_data["election_id"],
            selections=serializer.validated_data["selections"],
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        return Response(
            {
                "vote_id": str(vote.id),
                "receipt_code": vote.receipt_code,
                "cast_at": vote.cast_at,
                "message": "Vote cast successfully."
            },
            status=status.HTTP_201_CREATED
        )


class VoteSelectionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = VoteSelectionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return VoteSelection.objects.select_related("vote", "ballot_option").filter(vote__voter=self.request.user)