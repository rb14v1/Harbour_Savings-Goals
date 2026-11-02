from decimal import Decimal

from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.goals.models import SavingsGoal
from apps.goals.services import (
    compute_progress_pct,
    compute_projected_completion_date,
    compute_saved_amount,
)


class DashboardView(APIView):
    """Aggregate view across all of the current user's active (non-archived)
    savings goals. Archived goals are excluded from the totals entirely,
    matching the "active goals" scope of this endpoint."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        goals = SavingsGoal.objects.filter(user=request.user, is_archived=False).prefetch_related("contributions")

        total_saved = Decimal("0")
        total_target = Decimal("0")
        goal_rows = []

        for goal in goals:
            saved = compute_saved_amount(goal)
            total_saved += saved
            total_target += goal.target_amount
            goal_rows.append({
                "id": goal.id,
                "name": goal.name,
                "saved_amount": saved,
                "target_amount": goal.target_amount,
                "progress_pct": compute_progress_pct(saved, goal.target_amount),
                "projected_completion_date": compute_projected_completion_date(goal, saved),
            })

        overall_progress_pct = compute_progress_pct(total_saved, total_target)

        return Response({
            "total_saved": total_saved,
            "total_target": total_target,
            "progress_pct": overall_progress_pct,
            "goals": goal_rows,
        })
