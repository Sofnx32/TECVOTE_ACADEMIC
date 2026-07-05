from django.contrib import admin
from .models import Faculty, Program, AcademicPeriod, VoterRegistry


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "name")
    search_fields = ("code", "name")
    ordering = ("name",)


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "name", "faculty")
    list_filter = ("faculty",)
    search_fields = ("code", "name", "faculty__name")
    ordering = ("name",)


@admin.register(AcademicPeriod)
class AcademicPeriodAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "start_date", "end_date", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)
    ordering = ("-start_date",)


@admin.register(VoterRegistry)
class VoterRegistryAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "program", "period", "semester", "is_eligible")
    list_filter = ("is_eligible", "period", "program__faculty")
    search_fields = ("user__email", "user__institutional_id", "program__name", "period__name")
    autocomplete_fields = ("user", "program", "period")