from rest_framework import serializers
from .models import Ballot, BallotPosition, BallotOption


class BallotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ballot
        fields = "__all__"


class BallotPositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BallotPosition
        fields = "__all__"


class BallotOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BallotOption
        fields = "__all__"