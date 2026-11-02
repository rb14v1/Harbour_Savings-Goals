# Savings Goal Tracker

A deliberately small savings-goal tracker. Single user role — every
logged-in user only ever sees their own goals and contributions. React +
Vite + TypeScript frontend, Django REST Framework backend, PostgreSQL
database. No Celery/Redis — there is no background work to run.

## Data model

- **User** — Django's `AbstractUser` with `email` as `USERNAME_FIELD`. No
  profile model; single role.
- **SavingsGoal** — `user`, `name`, `target_amount`, `target_date`
  (optional), `created_at`, `is_archived` (default `False`).
- **Contribution** — `goal`, `amount` (must be `> 0`), `date`, `note`
  (optional).

`saved_amount`, `progress_pct` and `projected_completion_date` are never
stored on the goal — they're always computed from the related
contributions (see `apps.goals.services`), so there's a single source of
truth.

- `progress_pct` is `saved_amount / target_amount * 100`, clamped to
  `[0, 100]` for display. The underlying `saved_amount` is **not** clamped,
  so over-saving a goal is still visible in the raw numbers.
- `projected_completion_date` is an **illustrative, not actuarial**
  projection: it estimates a flat average monthly contribution rate as
  `total saved / number of distinct calendar months with at least one
  contribution`, then extrapolates forward from today. It ignores trends,
  seasonality and compounding — see the docstring in
  `backend/apps/goals/services.py` for the full assumption. It is `null`
  when the goal has no contribution history yet, has already reached its
  target, or has a target of `0`.

## Demo data

A data migration (`apps/goals/migrations/0002_seed_demo_data.py`) seeds one
demo user and a few goals/contributions on first `migrate`, so the app has
something to show immediately:

- Login: `demo@example.com` / `demo12345`
- Goals: **Emergency Fund** (target $5,000, 4 months of contributions),
  **Vacation** (target $2,000, 2 months of contributions), **New Laptop**
  (target $1,500, archived, no contributions — demonstrates the archive
  feature).

The migration is idempotent (`get_or_create` throughout), so re-running
`migrate` never creates duplicates.

## REST API

- `POST /api/auth/register/`, `POST /api/auth/login/` (JWT),
  `POST /api/auth/refresh/`, `POST /api/auth/logout/`, `GET /api/auth/me/`
- `/api/goals/` — list/create/retrieve/update/delete, `?archived=true|false`
  - `POST /api/goals/{id}/archive/`, `POST /api/goals/{id}/unarchive/`
  - `GET`/`POST /api/goals/{id}/contributions/` — nested list/create for
    that goal's contributions
- `/api/contributions/` — flat list/create/retrieve/update/delete,
  `?goal=<id>`, scoped to the current user's goals either way
- `GET /api/dashboard/` — total saved and total target across all
  **active (non-archived)** goals, overall `progress_pct`, and a per-goal
  breakdown (`name`, `saved_amount`, `target_amount`, `progress_pct`,
  `projected_completion_date`)

Every ViewSet scopes its queryset to `request.user` (directly for goals, via
the parent goal's `user` for contributions) — there is no cross-user access
even by guessing another user's object ID. See
`backend/apps/goals/tests/test_goals_api.py::GoalIsolationTests` and
`backend/apps/dashboard/tests/test_dashboard.py` for the isolation tests.

## Running locally with Docker (Postgres)

```bash
cp .env.example .env
docker compose up --build
```

Backend on http://localhost:8000, frontend on http://localhost:5173.

## Running the backend without Docker (dev-only SQLite override)

No Postgres/Docker needed for this — same `USE_SQLITE` pattern used by the
sibling apps in this workspace. **Never set `USE_SQLITE=True` in
docker-compose or production.**

```bash
cd backend
python -m venv venv
source venv/Scripts/activate   # Windows Git Bash; use venv\Scripts\activate.bat on cmd

pip install -r requirements.txt

export USE_SQLITE=True
export DJANGO_SETTINGS_MODULE=config.settings.dev

python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py test
python manage.py runserver
```

## Running the frontend

```bash
cd frontend
npm install
npm run dev      # dev server on :5173
npm run build    # production build (tsc -b && vite build)
```

Set `VITE_API_BASE_URL` (see `frontend/.env.example`) if the backend isn't
at `http://localhost:8000/api`.

## Auth trade-off (dev-only)

The access token is kept in memory only; the refresh token is kept in
`localStorage` and the client refreshes on a 401. A real deployment would
instead issue the refresh token as an httpOnly cookie from the backend —
this simplified pattern (same as the sibling apps in this workspace) is a
deliberate trade-off for a small demo app, not a recommendation for
production.

## Not set up here (left for real Postgres/Docker setup)

This app was built and verified against SQLite only (no Docker/Postgres
available in the build environment). Before using it for real:

- `docker compose up --build` has not been run/verified end-to-end.
- No `.env` has been created from `.env.example`.
- No migration has been run against actual Postgres (only SQLite).
