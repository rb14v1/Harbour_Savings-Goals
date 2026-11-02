from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.goals.models import Contribution, SavingsGoal
from common.test_utils import auth_client, create_user


class GoalIsolationTests(APITestCase):
    """Cross-user isolation: a user must never see, modify, or be able to
    attach contributions to another user's goals."""

    def setUp(self):
        self.user_a = create_user(email="a@example.com")
        self.user_b = create_user(email="b@example.com")
        self.goal_a = SavingsGoal.objects.create(user=self.user_a, name="A's goal", target_amount="1000.00")
        Contribution.objects.create(goal=self.goal_a, amount="100.00", date="2026-10-01")

    def test_user_cannot_list_other_users_goals(self):
        client = auth_client(self.user_b)
        response = client.get(reverse("goal-list"))
        ids = [row["id"] for row in response.data["results"]]
        self.assertNotIn(self.goal_a.id, ids)

    def test_user_cannot_retrieve_other_users_goal_by_id(self):
        client = auth_client(self.user_b)
        response = client.get(reverse("goal-detail", args=[self.goal_a.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cannot_update_other_users_goal(self):
        client = auth_client(self.user_b)
        response = client.patch(reverse("goal-detail", args=[self.goal_a.id]), {"name": "Hijacked"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cannot_delete_other_users_goal(self):
        client = auth_client(self.user_b)
        response = client.delete(reverse("goal-detail", args=[self.goal_a.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(SavingsGoal.objects.filter(pk=self.goal_a.id).exists())

    def test_user_cannot_archive_other_users_goal(self):
        client = auth_client(self.user_b)
        response = client.post(reverse("goal-archive", args=[self.goal_a.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cannot_list_other_users_contributions_via_nested_route(self):
        client = auth_client(self.user_b)
        response = client.get(reverse("goal-contributions", args=[self.goal_a.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cannot_create_contribution_against_other_users_goal(self):
        client = auth_client(self.user_b)
        response = client.post(reverse("contribution-list"), {
            "goal": self.goal_a.id, "amount": "50.00", "date": "2026-10-10",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_cannot_see_other_users_contributions_in_flat_list(self):
        client = auth_client(self.user_b)
        response = client.get(reverse("contribution-list"))
        ids = [row["id"] for row in response.data["results"]]
        contribution_id = Contribution.objects.get(goal=self.goal_a).id
        self.assertNotIn(contribution_id, ids)


class GoalProgressSerializationTests(APITestCase):
    def setUp(self):
        self.user = create_user(email="p@example.com")

    def test_goal_serializer_exposes_computed_fields(self):
        goal = SavingsGoal.objects.create(user=self.user, name="Gadget", target_amount="200.00")
        Contribution.objects.create(goal=goal, amount="50.00", date="2026-10-01")
        client = auth_client(self.user)
        response = client.get(reverse("goal-detail", args=[goal.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(response.data["saved_amount"]), Decimal("50.00"))
        self.assertEqual(Decimal(response.data["progress_pct"]), Decimal("25"))

    def test_archive_action_sets_is_archived(self):
        goal = SavingsGoal.objects.create(user=self.user, name="Archive me", target_amount="200.00")
        client = auth_client(self.user)
        response = client.post(reverse("goal-archive", args=[goal.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_archived"])
        goal.refresh_from_db()
        self.assertTrue(goal.is_archived)

    def test_create_goal_assigns_current_user(self):
        client = auth_client(self.user)
        response = client.post(reverse("goal-list"), {"name": "New", "target_amount": "300.00"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        goal = SavingsGoal.objects.get(id=response.data["id"])
        self.assertEqual(goal.user_id, self.user.id)

    def test_contribution_amount_must_be_positive(self):
        goal = SavingsGoal.objects.create(user=self.user, name="Positive only", target_amount="200.00")
        client = auth_client(self.user)
        response = client.post(reverse("goal-contributions", args=[goal.id]), {
            "amount": "-5.00", "date": "2026-10-01",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_nested_contribution_create_and_list(self):
        goal = SavingsGoal.objects.create(user=self.user, name="Nested", target_amount="200.00")
        client = auth_client(self.user)
        create_response = client.post(reverse("goal-contributions", args=[goal.id]), {
            "amount": "25.00", "date": "2026-10-05", "note": "test",
        })
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED, create_response.data)

        list_response = client.get(reverse("goal-contributions", args=[goal.id]))
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 1)
        self.assertEqual(list_response.data[0]["amount"], "25.00")
