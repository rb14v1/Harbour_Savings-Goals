from rest_framework import serializers

from apps.goals.models import Contribution, SavingsGoal
from apps.goals.services import (
    compute_progress_pct,
    compute_projected_completion_date,
    compute_saved_amount,
)


class SavingsGoalSerializer(serializers.ModelSerializer):
    saved_amount = serializers.SerializerMethodField()
    progress_pct = serializers.SerializerMethodField()
    projected_completion_date = serializers.SerializerMethodField()

    class Meta:
        model = SavingsGoal
        fields = [
            "id",
            "name",
            "target_amount",
            "target_date",
            "created_at",
            "is_archived",
            "saved_amount",
            "progress_pct",
            "projected_completion_date",
        ]
        read_only_fields = ["id", "created_at", "is_archived"]

    def validate_target_amount(self, value):
        if value < 0:
            raise serializers.ValidationError("Target amount cannot be negative.")
        return value

    def get_saved_amount(self, goal):
        return compute_saved_amount(goal)

    def get_progress_pct(self, goal):
        saved = compute_saved_amount(goal)
        return compute_progress_pct(saved, goal.target_amount)

    def get_projected_completion_date(self, goal):
        saved = compute_saved_amount(goal)
        return compute_projected_completion_date(goal, saved)


class ContributionSerializer(serializers.ModelSerializer):
    goal = serializers.PrimaryKeyRelatedField(queryset=SavingsGoal.objects.all())

    class Meta:
        model = Contribution
        fields = ["id", "goal", "amount", "date", "note", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def validate_goal(self, value):
        request = self.context.get("request")
        if request is not None and value.user_id != request.user.id:
            raise serializers.ValidationError("Goal not found.")
        return value
