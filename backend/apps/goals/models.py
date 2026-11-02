from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class SavingsGoal(models.Model):
    """A single savings target for one user.

    `saved_amount` / `progress_pct` / `projected_completion_date` are never
    stored - they are always derived from the related Contribution rows (see
    apps.goals.services) so there is a single source of truth and no risk of
    a cached total drifting out of sync with the ledger of contributions.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="savings_goals")
    name = models.CharField(max_length=150)
    target_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0"))])
    target_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_archived = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.user.email})"


class Contribution(models.Model):
    """A single deposit towards a SavingsGoal. Amount must be strictly
    positive - withdrawals aren't modelled in this demo app."""

    goal = models.ForeignKey(SavingsGoal, on_delete=models.CASCADE, related_name="contributions")
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    date = models.DateField()
    note = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.amount} towards {self.goal.name} on {self.date}"
