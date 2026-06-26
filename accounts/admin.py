from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("id", "username", "role", "email", "create_time", "is_active")
    list_filter = ("role", "is_active")
    search_fields = ("username", "email")
    ordering = ("-create_time",)
    fieldsets = UserAdmin.fieldsets + (
        ("额外信息", {"fields": ("role", "create_time")}),
    )
    readonly_fields = ("create_time",)
