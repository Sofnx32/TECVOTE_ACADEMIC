from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from apps.elections.permissions import IsElectionManagerOrReadOnly
from .models import AuditLog, OneTimeToken
from .serializers import AuditLogSerializer, OneTimeTokenSerializer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.select_related("actor", "election").all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsElectionManagerOrReadOnly]


class OneTimeTokenViewSet(viewsets.ModelViewSet):
    queryset = OneTimeToken.objects.select_related("user", "election").all()
    serializer_class = OneTimeTokenSerializer
    permission_classes = [IsAuthenticated, IsElectionManagerOrReadOnly]