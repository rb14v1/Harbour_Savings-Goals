"""Demo-data seed (data migration).

Creates one demo user plus a handful of savings goals and contributions so
the dashboard/progress/projection logic has something real to show out of
the box (e.g. right after `docker compose up` or a fresh `migrate`).

Idempotent: every object is created with get_or_create keyed on fields that
uniquely identify it for this seed, so re-running `migrate` (or running it
against a database that already has this data) does not create duplicates
or raise an error.

Demo login: demo@example.com / demo12345
"""
from datetime import date, timedelta

from django.db import migrations


def seed_demo_data(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    SavingsGoal = apps.get_model("goals", "SavingsGoal")
    Contribution = apps.get_model("goals", "Contribution")

    user, created = User.objects.get_or_create(
        email="demo@example.com",
        defaults={"first_name": "Demo", "last_name": "User", "is_active": True},
    )
    if created:
        # Historical model manager doesn't carry the custom create_user/
        # set_password helpers reliably across all Django versions, so hash
        # the password directly with the same hasher Django uses by default.
        from django.contrib.auth.hashers import make_password

        user.password = make_password("demo12345")
        user.save()

    today = date.today()

    def months_ago(n: int) -> date:
        year = today.year
        month = today.month - n
        while month <= 0:
            month += 12
            year -= 1
        day = min(today.day, 28)
        return date(year, month, day)

    emergency_fund, _ = SavingsGoal.objects.get_or_create(
        user=user,
        name="Emergency Fund",
        defaults={"target_amount": "5000.00", "target_date": None, "is_archived": False},
    )
    vacation, _ = SavingsGoal.objects.get_or_create(
        user=user,
        name="Vacation",
        defaults={"target_amount": "2000.00", "target_date": today + timedelta(days=180), "is_archived": False},
    )
    new_laptop, _ = SavingsGoal.objects.get_or_create(
        user=user,
        name="New Laptop",
        defaults={"target_amount": "1500.00", "target_date": None, "is_archived": True},
    )

    # Spread a few contributions across recent months for two goals so the
    # progress/projection math has real history to work from.
    emergency_fund_contributions = [
        (months_ago(3), "300.00", "Initial deposit"),
        (months_ago(2), "300.00", ""),
        (months_ago(1), "400.00", ""),
        (months_ago(0), "500.00", "Payday transfer"),
    ]
    for contribution_date, amount, note in emergency_fund_contributions:
        Contribution.objects.get_or_create(
            goal=emergency_fund, date=contribution_date, amount=amount,
            defaults={"note": note},
        )

    vacation_contributions = [
        (months_ago(2), "250.00", "Started saving"),
        (months_ago(1), "250.00", ""),
    ]
    for contribution_date, amount, note in vacation_contributions:
        Contribution.objects.get_or_create(
            goal=vacation, date=contribution_date, amount=amount,
            defaults={"note": note},
        )

    # New Laptop is archived and intentionally left with no contributions,
    # to demonstrate the archive feature alongside goals that have history.
    del new_laptop


def unseed_demo_data(apps, schema_editor):
    """Reverse migration: remove exactly the demo user and (via cascade)
    their goals/contributions. Safe no-op if already removed."""
    User = apps.get_model("accounts", "User")
    User.objects.filter(email="demo@example.com").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("goals", "0001_initial"),
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_demo_data, unseed_demo_data),
    ]
