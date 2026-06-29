from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ["id", "username", "role", "is_disabled", "create_time"]
    list_filter = ["role", "is_disabled"]
    search_fields = ["username"]
    ordering = ["-create_time"]
