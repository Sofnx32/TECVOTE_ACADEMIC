from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Election, Position, CandidateList, Candidacy, ElectionRule
from .serializers import (
    ElectionSerializer,
    PositionSerializer,
    CandidateListSerializer,
    CandidacySerializer,
    ElectionRuleSerializer,
)
from .permissions import IsElectionManagerOrReadOnly


class ElectionViewSet(viewsets.ModelViewSet):
    queryset = Election.objects.select_related("period", "faculty", "program", "created_by").all()
    serializer_class = ElectionSerializer
    permission_classes = [IsAuthenticated, IsElectionManagerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class PositionViewSet(viewsets.ModelViewSet):
    queryset = Position.objects.select_related("election").all()
    serializer_class = PositionSerializer
    permission_classes = [IsAuthenticated, IsElectionManagerOrReadOnly]


class CandidateListViewSet(viewsets.ModelViewSet):
    queryset = CandidateList.objects.select_related("election").all()
    serializer_class = CandidateListSerializer
    permission_classes = [IsAuthenticated, IsElectionManagerOrReadOnly]


class CandidacyViewSet(viewsets.ModelViewSet):
    queryset = Candidacy.objects.select_related("position", "candidate_list", "user").all()
    serializer_class = CandidacySerializer
    permission_classes = [IsAuthenticated, IsElectionManagerOrReadOnly]


class ElectionRuleViewSet(viewsets.ModelViewSet):
    queryset = ElectionRule.objects.select_related("election").all()
    serializer_class = ElectionRuleSerializer
    permission_classes = [IsAuthenticated, IsElectionManagerOrReadOnly]