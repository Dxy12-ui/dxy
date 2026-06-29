from django.contrib import admin
from .models import PlantCategory, PlantInfo, UserCollect, SearchHistory, PlantFeedback, OperationLog


@admin.register(PlantCategory)
class PlantCategoryAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "parent", "sort_order"]
    list_filter = ["parent"]
    search_fields = ["name"]


@admin.register(PlantInfo)
class PlantInfoAdmin(admin.ModelAdmin):
    list_display = ["id", "name_cn", "category", "status", "view_count", "update_time"]
    list_filter = ["status", "category", "is_toxic", "is_protected"]
    search_fields = ["name_cn", "name_en", "alias"]
    ordering = ["-update_time"]


@admin.register(UserCollect)
class UserCollectAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "plant", "create_time"]


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "keyword", "search_type", "create_time"]


@admin.register(PlantFeedback)
class PlantFeedbackAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "plant", "status", "create_time"]
    list_filter = ["status"]


@admin.register(OperationLog)
class OperationLogAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "action", "target_type", "target_id", "create_time"]
    list_filter = ["action"]
