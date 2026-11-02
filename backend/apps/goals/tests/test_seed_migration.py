"""Verifies the demo-data RunPython migration (0002_seed_demo_data) produced
the expected rows. Since `manage.py test` builds the test database by
running all migrations (including data migrations), this data is already
present by the time these tests run - no fixture loading needed."""
from decimal import Decimal

from django.test import TestCase

from apps.accounts.models import User
from apps.goals.models import SavingsGoal


class SeedMigrationTests(TestCase):
    def test_demo_user_exists_with_expected_password(self):
        user = User.objects.get(email="demo@example.com")
        self.assertTrue(user.check_password("demo12345"))

    def test_demo_user_has_three_goals(self):
        user = User.objects.get(email="demo@example.com")
        self.assertEqual(SavingsGoal.objects.filter(user=user).count(), 3)

    def test_one_goal_is_archived(self):
        user = User.objects.get(email="demo@example.com")
        archived = SavingsGoal.objects.filter(user=user, is_archived=True)
        self.assertEqual(archived.count(), 1)
        self.assertEqual(archived.first().name, "New Laptop")

    def test_at_least_two_goals_have_contribution_history(self):
        user = User.objects.get(email="demo@example.com")
        goals_with_contributions = [
            g for g in SavingsGoal.objects.filter(user=user) if g.contributions.exists()
        ]
        self.assertGreaterEqual(len(goals_with_contributions), 2)

    def test_emergency_fund_target_and_contributions(self):
        user = User.objects.get(email="demo@example.com")
        goal = SavingsGoal.objects.get(user=user, name="Emergency Fund")
        self.assertEqual(goal.target_amount, Decimal("5000.00"))
        self.assertFalse(goal.is_archived)
        self.assertEqual(goal.contributions.count(), 4)
