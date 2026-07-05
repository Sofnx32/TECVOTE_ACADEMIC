from django.contrib import admin
from .models import Tally, ElectionResult


@admin.register(Tally)
class TallyAdmin(admin.ModelAdmin):
    list_display = ("id", "election", "position", "option", "votes_count", "updated_at")
    list_filter = ("election", "position")
    autocomplete_fields = ("election", "position", "option")
    readonly_fields = ("updated_at",)


@admin.register(ElectionResult)
class ElectionResultAdmin(admin.ModelAdmin):
    list_display = ("id", "election", "total_voters", "total_votes_cast", "turnout_percentage", "certified_at", "published_at")
    autocomplete_fields = ("election",)