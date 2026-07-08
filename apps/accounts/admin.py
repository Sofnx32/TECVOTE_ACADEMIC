# apps/accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ("email", "username", "role", "institutional_id", "is_verified", "is_staff")
    list_filter = ("role", "is_verified", "is_staff", "is_superuser", "is_active")
    ordering = ("email",)
    search_fields = ("email", "username", "institutional_id")

    fieldsets = UserAdmin.fieldsets + (
        ("Información académica", {"fields": ("role", "institutional_id", "is_verified")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Información académica", {"fields": ("email", "role", "institutional_id", "is_verified")}),
    )