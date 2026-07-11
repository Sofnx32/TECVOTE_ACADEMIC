from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction
from rest_framework import generics, permissions
from apps.academic.models import Faculty, AcademicPeriod
from .serializers import FacultySerializer, AcademicPeriodSerializer
from .models import Election, Position, CandidateList, Candidacy, ElectionRule
from apps.security.models import AuditLog  

from .serializers import (
    ElectionListSerializer,
    ElectionDetailSerializer,
    ElectionCreateSerializer,
    PositionSerializer,
    CandidateListSerializer,
    CandidacySerializer,
    ElectionRuleSerializer,
)
from .permissions import IsElectionManagerOrReadOnly


class ElectionViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

    def _create_audit_log(self, request, election, action_type, metadata=None):
        try:
            AuditLog.objects.create(
                actor=request.user,
                election=election,
                action=action_type,
                ip_address=self._get_client_ip(request),
                metadata=metadata or {}
            )
        except Exception:
            pass

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Election.objects.select_related(
                'period', 'faculty', 'program', 'created_by'
            ).all().order_by("-created_at")
        
        user_organization = getattr(user, 'organization', None)
        if user_organization:
            return Election.objects.filter(
                created_by__organization=user_organization
            ).select_related(
                'period', 'faculty', 'program', 'created_by'
            ).order_by("-created_at")
            
        return Election.objects.filter(created_by=user).select_related(
            'period', 'faculty', 'program', 'created_by'
        ).order_by("-created_at")
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ElectionListSerializer
        elif self.action == 'create':
            return ElectionCreateSerializer
        return ElectionDetailSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            election = serializer.save(created_by=request.user)
            self._create_audit_log(
                request=request, 
                election=election, 
                action_type=AuditLog.ActionType.CREATE_ELECTION,
                metadata={"title": election.title}
            )
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        election = self.get_object()
        
        if election.status not in [Election.Status.DRAFT, Election.Status.SCHEDULED]:
            return Response(
                {'error': 'Solo se pueden activar elecciones en borrador o programadas'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if election.start_at > timezone.now():
            return Response(
                {'error': 'No se puede activar manualmente; la fecha de inicio es futura.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            election.status = Election.Status.OPEN
            election.save()
            self._create_audit_log(
                request=request, 
                election=election, 
                action_type=AuditLog.ActionType.OPEN_ELECTION
            )
            
        return Response({'message': 'La elección ha sido abierta con éxito.'})
    
    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        election = self.get_object()
        
        if election.status != Election.Status.OPEN:
            return Response(
                {'error': 'Solo se pueden cerrar elecciones que estén actualmente abiertas'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            election.status = Election.Status.CLOSED
            election.save()
            self._create_audit_log(
                request=request, 
                election=election, 
                action_type=AuditLog.ActionType.CLOSE_ELECTION
            )
            
        return Response({'message': 'La elección ha sido cerrada.'})
    
    @action(detail=True, methods=['post'])
    def certify(self, request, pk=None):
        election = self.get_object()
        
        if election.status != Election.Status.CLOSED:
            return Response(
                {'error': 'Solo se pueden certificar elecciones cerradas'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            election.status = Election.Status.CERTIFIED
            election.save()
            self._create_audit_log(
                request=request, 
                election=election, 
                action_type=AuditLog.ActionType.CERTIFY_RESULT
            )
            
        return Response({'message': 'Resultados de la elección certificados correctamente.'})


class PositionViewSet(viewsets.ModelViewSet):
    serializer_class = PositionSerializer
    permission_classes = [IsAuthenticated, IsElectionManagerOrReadOnly]
    
    def get_queryset(self):
        # Intentamos capturar el parámetro de todas las formas posibles en que DRF anida URLs
        election_id = (
            self.kwargs.get('election_pk') or 
            self.kwargs.get('pk') or 
            self.kwargs.get('election_id')
        )
        
        # Forzamos la conversión a string y limpiamos espacios por si acaso
        election_str = str(election_id).strip() if election_id else ""
        
        # Si no hay ID, o es el texto literal 'undefined', o no es numérico: frenamos el query
        if not election_str or election_str == 'undefined' or not election_str.isdigit():
            return Position.objects.none()
            
        return Position.objects.filter(election_id=int(election_str))


class CandidateListViewSet(viewsets.ModelViewSet):
    serializer_class = CandidateListSerializer
    permission_classes = [IsAuthenticated, IsElectionManagerOrReadOnly]
    
    def get_queryset(self):
        election_id = self.kwargs.get('election_pk') or self.kwargs.get('pk')
        # Si el ID no es enteramente numérico (ej. 'undefined'), evitamos romper la BD
        if not election_id or not str(election_id).isdigit():
            return CandidateList.objects.none()
        return CandidateList.objects.filter(election_id=election_id)


class CandidacyViewSet(viewsets.ModelViewSet):
    serializer_class = CandidacySerializer
    permission_classes = [IsAuthenticated, IsElectionManagerOrReadOnly]
    
    def get_queryset(self):
        position_id = self.kwargs.get('position_pk') or self.kwargs.get('pk')
        # Si el ID no es enteramente numérico (ej. 'undefined'), evitamos romper la BD
        if not position_id or not str(position_id).isdigit():
            return Candidacy.objects.none()
        return Candidacy.objects.filter(position_id=position_id)


class ElectionRuleViewSet(viewsets.ModelViewSet):
    serializer_class = ElectionRuleSerializer
    permission_classes = [IsAuthenticated, IsElectionManagerOrReadOnly]
    
    def get_queryset(self):
        election_id = self.kwargs.get('election_pk') or self.kwargs.get('pk')
        # Si el ID no es enteramente numérico (ej. 'undefined'), evitamos romper la BD
        if not election_id or not str(election_id).isdigit():
            return ElectionRule.objects.none()
        return ElectionRule.objects.filter(election_id=election_id)
    def perform_create(self, serializer):
        election_id = self.kwargs.get('election_pk')
        serializer.save(election_id=election_id)


class FacultyListCreateView(generics.ListCreateAPIView):
    queryset = Faculty.objects.all()
    serializer_class = FacultySerializer
    permission_classes = [permissions.IsAuthenticated]


class AcademicPeriodListCreateView(generics.ListCreateAPIView):
    queryset = AcademicPeriod.objects.all().order_by('-start_date')
    serializer_class = AcademicPeriodSerializer
    permission_classes = [permissions.IsAuthenticated]