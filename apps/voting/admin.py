from django.contrib import admin
from .models import VotingSession, Vote, VoteSelection


@admin.register(VotingSession)
class VotingSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "election", "voter", "started_at", "completed_at", "is_successful")
    list_filter = ("is_successful", "election")
    search_fields = ("voter__email", "voter__institutional_id")
    autocomplete_fields = ("election", "voter")


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ("id", "election", "voter", "cast_at", "receipt_code")
    list_filter = ("election",)
    search_fields = ("receipt_code", "voter__email")
    autocomplete_fields = ("election", "voter", "session")
    readonly_fields = ("cast_at",)


@admin.register(VoteSelection)
class VoteSelectionAdmin(admin.ModelAdmin):
    list_display = ("id", "vote", "ballot_option")
    autocomplete_fields = ("vote", "ballot_option")