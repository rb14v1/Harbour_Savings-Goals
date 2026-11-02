from django.contrib import admin

from apps.goals.models import Contribution, SavingsGoal


@admin.register(SavingsGoal)
class SavingsGoalAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "target_amount", "is_archived", "created_at"]
    list_filter = ["is_archived"]
    search_fields = ["name", "user__email"]


@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = ["goal", "amount", "date"]
    list_filter = ["date"]
    search_fields = ["goal__name"]
