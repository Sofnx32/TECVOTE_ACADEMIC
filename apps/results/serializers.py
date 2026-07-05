from rest_framework import serializers
from .models import Tally, ElectionResult


class TallySerializer(serializers.ModelSerializer):
    class Meta:
        model = Tally
        fields = "__all__"


class ElectionResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElectionResult
        fields = "__all__"