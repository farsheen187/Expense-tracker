from django.contrib import admin

from .models import Budget, Category, Transaction


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "user", "created_at")
    list_filter = ("type",)
    search_fields = ("name", "user__username")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("type", "amount", "category", "date", "user")
    list_filter = ("type", "date")
    search_fields = ("note", "user__username")


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ("category", "month", "year", "limit_amount", "user")
    list_filter = ("year", "month")
