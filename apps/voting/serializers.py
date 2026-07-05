from rest_framework import serializers
from .models import VotingSession, Vote, VoteSelection


class VotingSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VotingSession
        fields = "__all__"


class VoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vote
        fields = "__all__"
        read_only_fields = ("id", "cast_at", "receipt_code", "payload_hash")


class VoteSelectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VoteSelection
        fields = "__all__"


class CastVoteSerializer(serializers.Serializer):
    election_id = serializers.IntegerField()
    selections = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False
    )