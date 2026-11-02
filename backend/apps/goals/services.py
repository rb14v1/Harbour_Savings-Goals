"""Pure calculation helpers for SavingsGoal progress and projection.

Kept separate from models/serializers so the (deliberately simple) math is
easy to find, unit-test and reason about in isolation.
"""
from __future__ import annotations

import calendar
import math
from datetime import date
from decimal import Decimal

from django.db.models import Sum


def add_months(start: date, months: int) -> date:
    """Returns `start` shifted forward by `months` whole calendar months,
    clamping the day to the last valid day of the resulting month (e.g. Jan
    31 + 1 month -> Feb 28/29, never a ValueError)."""
    month_index = start.month - 1 + months
    year = start.year + month_index // 12
    month = month_index % 12 + 1
    day = min(start.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def compute_saved_amount(goal) -> Decimal:
    """Sum of all contributions for `goal`. Over-saving (sum > target) is
    allowed and reported as-is - only `progress_pct` is clamped for display."""
    total = goal.contributions.aggregate(total=Sum("amount"))["total"]
    return total if total is not None else Decimal("0")


def compute_progress_pct(saved_amount: Decimal, target_amount: Decimal) -> Decimal:
    """Percentage of target saved, clamped to [0, 100] for display. The
    underlying saved_amount is never clamped, so over-saving is still
    visible in the raw numbers even though the percentage caps at 100."""
    target_amount = Decimal(str(target_amount)) if target_amount is not None else None
    if not target_amount or target_amount <= 0:
        return Decimal("0")
    pct = (saved_amount / target_amount) * Decimal("100")
    if pct < 0:
        return Decimal("0")
    return min(pct, Decimal("100"))


def compute_projected_completion_date(goal, saved_amount: Decimal, today: date | None = None) -> date | None:
    """Illustrative, NOT actuarial, projection of when `goal` will reach its
    target.

    ASSUMPTION (deliberately simple): a flat "average monthly contribution
    rate" is estimated as

        total saved so far / number of distinct calendar months (YYYY-MM)
        that contain at least one contribution

    i.e. every month that saw *any* contribution counts once, regardless of
    how much was contributed that month or how long ago it was. This ignores
    trends, seasonality, compounding/interest and gaps between contribution
    months. It is a simple run-rate extrapolation meant to illustrate the
    feature, not a financial forecast.

    Returns None when:
      - target_amount is 0 or less (rate/percentage is undefined)
      - the goal has already reached (or passed) its target
      - there is no contribution history yet to extrapolate from
      - the computed average monthly rate is 0 (target can never be reached
        at the current observed rate)
    """
    today = today or date.today()
    target = goal.target_amount
    target = Decimal(str(target)) if target is not None else None
    if target is None or target <= 0:
        return None

    remaining = target - saved_amount
    if remaining <= 0:
        return None

    contribution_dates = list(goal.contributions.values_list("date", flat=True))
    if not contribution_dates:
        return None

    distinct_months = {(d.year, d.month) for d in contribution_dates}
    months_with_activity = len(distinct_months)
    if months_with_activity <= 0:
        return None

    avg_monthly_rate = saved_amount / Decimal(months_with_activity)
    if avg_monthly_rate <= 0:
        return None

    months_needed = math.ceil(remaining / avg_monthly_rate)
    if months_needed <= 0:
        return None

    return add_months(today, int(months_needed))
