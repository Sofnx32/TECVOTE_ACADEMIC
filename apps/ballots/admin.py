from django.contrib import admin
from .models import Ballot, BallotPosition, BallotOption


class BallotPositionInline(admin.TabularInline):
    model = BallotPosition
    extra = 1


@admin.register(Ballot)
class BallotAdmin(admin.ModelAdmin):
    list_display = ("id", "election", "version", "is_active", "generated_at")
    list_filter = ("is_active", "election")
    search_fields = ("election__title",)
    autocomplete_fields = ("election",)
    inlines = [BallotPositionInline]


@admin.register(BallotPosition)
class BallotPositionAdmin(admin.ModelAdmin):
    list_display = ("id", "ballot", "position", "order")
    list_filter = ("ballot__election",)
    autocomplete_fields = ("ballot", "position")
    search_fields = ("ballot__election__title", "position__name")


@admin.register(BallotOption)
class BallotOptionAdmin(admin.ModelAdmin):
    list_display = ("id", "ballot_position", "option_type", "candidate_list", "label")
    list_filter = ("option_type", "ballot_position__ballot__election")
    search_fields = ("label", "candidate_list__name")
    autocomplete_fields = ("ballot_position", "candidate_list")