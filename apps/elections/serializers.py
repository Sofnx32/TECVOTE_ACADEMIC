from rest_framework import serializers
from .models import Election, Position, CandidateList, Candidacy, ElectionRule


class ElectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Election
        fields = "__all__"
        read_only_fields = ("id", "created_at", "created_by")


class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = "__all__"


class CandidateListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateList
        fields = "__all__"


class CandidacySerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidacy
        fields = "__all__"


class ElectionRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElectionRule
        fields = "__all__"