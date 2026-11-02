from rest_framework.routers import DefaultRouter

from apps.goals.views import SavingsGoalViewSet

router = DefaultRouter()
router.register(r"", SavingsGoalViewSet, basename="goal")

urlpatterns = router.urls
