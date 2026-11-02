from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.auth_urls")),
    path("api/", include("apps.accounts.urls")),
    path("api/goals/", include("apps.goals.urls")),
    path("api/contributions/", include("apps.goals.contribution_urls")),
    path("api/dashboard/", include("apps.dashboard.urls")),
]
