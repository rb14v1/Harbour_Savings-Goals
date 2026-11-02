from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.goals.models import Contribution, SavingsGoal
from common.test_utils import auth_client, create_user


class DashboardAggregationTests(APITestCase):
    def setUp(self):
        self.user = create_user(email="dash@example.com")
        self.other_user = create_user(email="other-dash@example.com")

        self.active_goal_1 = SavingsGoal.objects.create(user=self.user, name="Active 1", target_amount="1000.00")
        self.active_goal_2 = SavingsGoal.objects.create(user=self.user, name="Active 2", target_amount="500.00")
        self.archived_goal = SavingsGoal.objects.create(
            user=self.user, name="Archived", target_amount="999.00", is_archived=True,
        )

        Contribution.objects.create(goal=self.active_goal_1, amount="250.00", date="2026-09-01")
        Contribution.objects.create(goal=self.active_goal_1, amount="250.00", date="2026-10-01")
        Contribution.objects.create(goal=self.active_goal_2, amount="100.00", date="2026-10-01")
        # Archived goal still has a contribution, but must not count toward totals.
        Contribution.objects.create(goal=self.archived_goal, amount="999.00", date="2026-01-01")

        # Other user's data must never leak in.
        other_goal = SavingsGoal.objects.create(user=self.other_user, name="Other", target_amount="100.00")
        Contribution.objects.create(goal=other_goal, amount="100.00", date="2026-10-01")

    def test_requires_auth(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_totals_exclude_archived_and_other_users(self):
        client = auth_client(self.user)
        response = client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(response.data["total_saved"]), Decimal("600.00"))
        self.assertEqual(Decimal(response.data["total_target"]), Decimal("1500.00"))
        self.assertEqual(Decimal(response.data["progress_pct"]), Decimal("40"))

    def test_goal_rows_present_for_active_goals_only(self):
        client = auth_client(self.user)
        response = client.get(reverse("dashboard"))
        names = {row["name"] for row in response.data["goals"]}
        self.assertEqual(names, {"Active 1", "Active 2"})

    def test_goal_row_shape(self):
        client = auth_client(self.user)
        response = client.get(reverse("dashboard"))
        row = next(r for r in response.data["goals"] if r["name"] == "Active 1")
        self.assertEqual(Decimal(row["saved_amount"]), Decimal("500.00"))
        self.assertEqual(Decimal(row["target_amount"]), Decimal("1000.00"))
        self.assertEqual(Decimal(row["progress_pct"]), Decimal("50"))
        self.assertIn("projected_completion_date", row)
