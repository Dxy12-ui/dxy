from django.contrib import admin
from .models import Category, Book, BorrowRecord


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "author", "category", "stock", "total_num", "create_time")
    list_filter = ("category",)
    search_fields = ("title", "author")
    ordering = ("-create_time",)


@admin.register(BorrowRecord)
class BorrowRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "book", "borrow_date", "return_date", "is_return")
    list_filter = ("is_return",)
    search_fields = ("user__username", "book__title")
    ordering = ("-borrow_date",)
