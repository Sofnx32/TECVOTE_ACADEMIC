from django.contrib import admin
from .models import Election, Position, CandidateList, Candidacy, ElectionRule


class PositionInline(admin.TabularInline):
    model = Position
    extra = 1


class CandidateListInline(admin.TabularInline):
    model = CandidateList
    extra = 1


@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "election_type", "status", "period", "start_at", "end_at")
    list_filter = ("status", "election_type", "period")
    search_fields = ("title", "description")
    autocomplete_fields = ("period", "faculty", "program", "created_by")
    inlines = [PositionInline, CandidateListInline]


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "election", "seats")
    list_filter = ("election",)
    search_fields = ("name", "election__title")
    autocomplete_fields = ("election",)


@admin.register(CandidateList)
class CandidateListAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "acronym", "election")
    list_filter = ("election",)
    search_fields = ("name", "acronym", "election__title")
    autocomplete_fields = ("election",)


@admin.register(Candidacy)
class CandidacyAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "position", "candidate_list", "order", "is_principal")
    list_filter = ("is_principal", "position__election")
    search_fields = ("user__email", "position__name", "candidate_list__name")
    autocomplete_fields = ("user", "position", "candidate_list")


@admin.register(ElectionRule)
class ElectionRuleAdmin(admin.ModelAdmin):
    list_display = ("id", "election", "allow_blank_vote", "allow_null_vote", "requires_2fa")
    list_filter = ("allow_blank_vote", "allow_null_vote", "requires_2fa")
    autocomplete_fields = ("election",)