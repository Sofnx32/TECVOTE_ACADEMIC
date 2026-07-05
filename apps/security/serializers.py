from rest_framework import serializers
from .models import AuditLog, OneTimeToken


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = "__all__"


class OneTimeTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = OneTimeToken
        fields = "__all__"