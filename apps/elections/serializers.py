from rest_framework import serializers
from django.db import transaction
from .models import Election, Position, CandidateList, Candidacy, ElectionRule
from apps.academic.models import Faculty, AcademicPeriod

class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ['id', 'name', 'description', 'seats']


class CandidateListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateList
        fields = ['id', 'name', 'acronym', 'motto', 'logo']


class CandidacySerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Candidacy
        fields = ['id', 'position', 'candidate_list', 'user', 'user_email', 'user_name', 'order', 'is_principal']


class ElectionRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElectionRule
        fields = '__all__'
        read_only_fields = ['election']


class ElectionListSerializer(serializers.ModelSerializer):
    """Serializer para listar elecciones (ligero/optimizado)."""
    period_name = serializers.CharField(source='period.name', read_only=True)
    faculty_name = serializers.CharField(source='faculty.name', read_only=True)
    program_name = serializers.CharField(source='program.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    positions_count = serializers.SerializerMethodField()
    candidate_lists_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Election
        fields = [
            'id', 'title', 'description', 'election_type', 'status',
            'period', 'period_name', 'faculty', 'faculty_name', 
            'program', 'program_name',
            'start_at', 'end_at',
            'created_by', 'created_by_name', 'created_at',
            'positions_count', 'candidate_lists_count'
        ]
    
    def get_positions_count(self, obj):
        return obj.positions.count()
    
    def get_candidate_lists_count(self, obj):
        return obj.candidate_lists.count()


class ElectionDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado para lectura completa con relaciones anidadas."""
    period_name = serializers.CharField(source='period.name', read_only=True)
    faculty_name = serializers.CharField(source='faculty.name', read_only=True)
    program_name = serializers.CharField(source='program.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    positions = PositionSerializer(many=True, read_only=True)
    candidate_lists = CandidateListSerializer(many=True, read_only=True)
    rules = ElectionRuleSerializer(read_only=True)
    
    class Meta:
        model = Election
        fields = [
            'id', 'title', 'description', 'election_type', 'status',
            'period', 'period_name', 'faculty', 'faculty_name',
            'program', 'program_name',
            'start_at', 'end_at',
            'created_by', 'created_by_name', 'created_at',
            'positions', 'candidate_lists', 'rules'
        ]


class ElectionCreateSerializer(serializers.ModelSerializer):
    """Serializer seguro para crear elecciones complejas en un solo paso."""
    positions = PositionSerializer(many=True, required=False)
    candidate_lists = CandidateListSerializer(many=True, required=False)
    rules = ElectionRuleSerializer(required=False)
    
    class Meta:
        model = Election
        fields = [
            'title', 'description', 'election_type',
            'period', 'faculty', 'program',
            'start_at', 'end_at',
            'positions', 'candidate_lists', 'rules'
        ]
        
    def create(self, validated_data):
        # Extraemos los datos anidados para manejarlos manualmente
        positions_data = validated_data.pop('positions', [])
        lists_data = validated_data.pop('candidate_lists', [])
        rules_data = validated_data.pop('rules', None)
        
        # Inyectamos el usuario logueado que viene del request de DRF
        request = self.context.get('request')
        if request and request.user:
            validated_data['created_by'] = request.user

        # Transacción atómica: si algo falla adentro, se revierte TODO en la base de datos
        with transaction.atomic():
            # 1. Crear la elección principal
            election = Election.objects.create(**validated_data)
            
            # 2. Crear los cargos asociados
            for pos_data in positions_data:
                Position.objects.create(election=election, **pos_data)
            
            # 3. Crear las listas de candidatos asociados
            for list_data in lists_data:
                CandidateList.objects.create(election=election, **list_data)
            
            # 4. Crear las reglas de la elección si se proporcionaron
            if rules_data:
                ElectionRule.objects.create(election=election, **rules_data)
            
        return election

class FacultySerializer(serializers.ModelSerializer):
    class Meta:
        model = Faculty
        fields = ['id', 'name', 'code']


class AcademicPeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicPeriod
        fields = ['id', 'name', 'start_date', 'end_date', 'is_active']