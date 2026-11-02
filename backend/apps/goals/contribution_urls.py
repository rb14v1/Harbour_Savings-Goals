from rest_framework.routers import DefaultRouter

from apps.goals.views import ContributionViewSet

router = DefaultRouter()
router.register(r"", ContributionViewSet, basename="contribution")

urlpatterns = router.urls
