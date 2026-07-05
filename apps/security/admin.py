from django.contrib import admin
from .models import AuditLog, OneTimeToken


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("id", "action", "actor", "election", "timestamp", "ip_address")
    list_filter = ("action", "timestamp")
    search_fields = ("actor__email", "metadata")
    autocomplete_fields = ("actor", "election")
    readonly_fields = ("timestamp",)


@admin.register(OneTimeToken)
class OneTimeTokenAdmin(admin.ModelAdmin):
    list_display = ("token", "user", "election", "created_at", "expires_at", "used_at", "is_used")
    list_filter = ("created_at", "expires_at", "used_at")
    search_fields = ("token", "user__email")
    autocomplete_fields = ("user", "election")
    readonly_fields = ("created_at", "is_used")