from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from apps.elections.permissions import IsElectionManagerOrReadOnly
from .models import Ballot, BallotPosition, BallotOption
from .serializers import BallotSerializer, BallotPositionSerializer, BallotOptionSerializer


class BallotViewSet(viewsets.ModelViewSet):
    queryset = Ballot.objects.select_related("election").all()
    serializer_class = BallotSerializer
    permission_classes = [IsAuthenticated, IsElectionManagerOrReadOnly]


class BallotPositionViewSet(viewsets.ModelViewSet):
    queryset = BallotPosition.objects.select_related("ballot", "position").all()
    serializer_class = BallotPositionSerializer
    permission_classes = [IsAuthenticated, IsElectionManagerOrReadOnly]


class BallotOptionViewSet(viewsets.ModelViewSet):
    queryset = BallotOption.objects.select_related("ballot_position", "candidate_list").all()
    serializer_class = BallotOptionSerializer
    permission_classes = [IsAuthenticated, IsElectionManagerOrReadOnly]