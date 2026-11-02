from datetime import date
from decimal import Decimal

from django.test import TestCase

from apps.goals.models import Contribution, SavingsGoal
from apps.goals.services import (
    add_months,
    compute_progress_pct,
    compute_projected_completion_date,
    compute_saved_amount,
)
from common.test_utils import create_user


class AddMonthsTests(TestCase):
    def test_simple_forward(self):
        self.assertEqual(add_months(date(2026, 1, 15), 2), date(2026, 3, 15))

    def test_wraps_year(self):
        self.assertEqual(add_months(date(2026, 11, 10), 3), date(2027, 2, 10))

    def test_clamps_end_of_month(self):
        # Jan 31 + 1 month -> Feb has no 31st, clamp to the 28th (2026 is not a leap year).
        self.assertEqual(add_months(date(2026, 1, 31), 1), date(2026, 2, 28))


class ProgressPctTests(TestCase):
    def test_zero_target_returns_zero(self):
        self.assertEqual(compute_progress_pct(Decimal("50"), Decimal("0")), Decimal("0"))

    def test_partial_progress(self):
        self.assertEqual(compute_progress_pct(Decimal("25"), Decimal("100")), Decimal("25"))

    def test_clamped_at_100_when_oversaved(self):
        self.assertEqual(compute_progress_pct(Decimal("150"), Decimal("100")), Decimal("100"))


class SavedAmountAndProjectionTests(TestCase):
    def setUp(self):
        self.user = create_user(email="svc@example.com")

    def test_saved_amount_sums_contributions(self):
        goal = SavingsGoal.objects.create(user=self.user, name="Test", target_amount="1000.00")
        Contribution.objects.create(goal=goal, amount="100.00", date="2026-09-01")
        Contribution.objects.create(goal=goal, amount="50.00", date="2026-10-01")
        self.assertEqual(compute_saved_amount(goal), Decimal("150.00"))

    def test_saved_amount_zero_with_no_contributions(self):
        goal = SavingsGoal.objects.create(user=self.user, name="Empty", target_amount="1000.00")
        self.assertEqual(compute_saved_amount(goal), Decimal("0"))

    def test_projection_none_with_no_contribution_history(self):
        goal = SavingsGoal.objects.create(user=self.user, name="No history", target_amount="1000.00")
        self.assertIsNone(compute_projected_completion_date(goal, Decimal("0")))

    def test_projection_none_when_target_already_reached(self):
        goal = SavingsGoal.objects.create(user=self.user, name="Reached", target_amount="100.00")
        Contribution.objects.create(goal=goal, amount="100.00", date="2026-10-01")
        saved = compute_saved_amount(goal)
        self.assertIsNone(compute_projected_completion_date(goal, saved))

    def test_projection_none_when_oversaved(self):
        goal = SavingsGoal.objects.create(user=self.user, name="Oversaved", target_amount="100.00")
        Contribution.objects.create(goal=goal, amount="150.00", date="2026-10-01")
        saved = compute_saved_amount(goal)
        self.assertEqual(saved, Decimal("150.00"))
        self.assertIsNone(compute_projected_completion_date(goal, saved))

    def test_projection_none_when_target_is_zero(self):
        goal = SavingsGoal.objects.create(user=self.user, name="ZeroTarget", target_amount="0.00")
        Contribution.objects.create(goal=goal, amount="10.00", date="2026-10-01")
        saved = compute_saved_amount(goal)
        self.assertIsNone(compute_projected_completion_date(goal, saved))

    def test_projection_extrapolates_from_distinct_contribution_months(self):
        # Two distinct months, 100 total saved -> avg rate 50/month.
        # Target 1000, remaining 900 -> ceil(900/50) = 18 months from "today".
        goal = SavingsGoal.objects.create(user=self.user, name="Projected", target_amount="1000.00")
        Contribution.objects.create(goal=goal, amount="50.00", date="2026-09-05")
        Contribution.objects.create(goal=goal, amount="50.00", date="2026-10-05")
        saved = compute_saved_amount(goal)
        today = date(2026, 11, 2)
        projected = compute_projected_completion_date(goal, saved, today=today)
        self.assertEqual(projected, add_months(today, 18))

    def test_multiple_contributions_same_month_count_once(self):
        # Same calendar month contributions still count as a single active
        # month for the averaging denominator (documented assumption).
        goal = SavingsGoal.objects.create(user=self.user, name="SameMonth", target_amount="1000.00")
        Contribution.objects.create(goal=goal, amount="40.00", date="2026-10-01")
        Contribution.objects.create(goal=goal, amount="60.00", date="2026-10-20")
        saved = compute_saved_amount(goal)
        self.assertEqual(saved, Decimal("100.00"))
        today = date(2026, 11, 2)
        # avg rate = 100 / 1 month = 100/month; remaining = 900; ceil(900/100) = 9
        projected = compute_projected_completion_date(goal, saved, today=today)
        self.assertEqual(projected, add_months(today, 9))
