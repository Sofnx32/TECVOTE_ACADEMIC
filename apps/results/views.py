from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from apps.elections.models import Election
from apps.elections.permissions import IsElectionManagerOrReadOnly
from .models import Tally, ElectionResult
from .serializers import TallySerializer, ElectionResultSerializer
from .permissions import IsElectionManager
from .services import close_election, certify_election_results, publish_election_results


class TallyViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TallySerializer
    permission_classes = [IsAuthenticated, IsElectionManagerOrReadOnly]

    def get_queryset(self):
        # Block visibility until election is published
        return (
            Tally.objects.select_related("election", "position", "option")
            .filter(election__status="PUBLISHED")
        )


class ElectionResultViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ElectionResultSerializer
    permission_classes = [IsAuthenticated, IsElectionManagerOrReadOnly]

    def get_queryset(self):
        # Block visibility until election is published
        return ElectionResult.objects.select_related("election").filter(election__status="PUBLISHED")


class ElectionLifecycleViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsElectionManager]

    @action(detail=False, methods=["post"], url_path="close")
    def close(self, request):
        election_id = request.data.get("election_id")
        election = get_object_or_404(Election, id=election_id)

        close_election(
            election=election,
            actor=request.user,
            ip_address=request.META.get("REMOTE_ADDR"),
        )
        return Response({"message": "Election closed successfully."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="certify")
    def certify(self, request):
        election_id = request.data.get("election_id")
        election = get_object_or_404(Election, id=election_id)

        result = certify_election_results(
            election=election,
            actor=request.user,
            ip_address=request.META.get("REMOTE_ADDR"),
        )
        return Response(
            {
                "message": "Election certified successfully.",
                "election_id": election.id,
                "turnout_percentage": str(result.turnout_percentage),
                "total_votes_cast": result.total_votes_cast,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"], url_path="publish")
    def publish(self, request):
        election_id = request.data.get("election_id")
        election = get_object_or_404(Election, id=election_id)

        result = publish_election_results(
            election=election,
            actor=request.user,
            ip_address=request.META.get("REMOTE_ADDR"),
        )
        return Response(
            {
                "message": "Election published successfully.",
                "election_id": election.id,
                "published_at": result.published_at,
                "report_pdf": result.report_pdf.url if result.report_pdf else None,
            },
            status=status.HTTP_200_OK,
        )