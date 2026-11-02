from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.goals.models import Contribution, SavingsGoal
from apps.goals.serializers import ContributionSerializer, SavingsGoalSerializer


class SavingsGoalViewSet(viewsets.ModelViewSet):
    serializer_class = SavingsGoalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = SavingsGoal.objects.filter(user=self.request.user).prefetch_related("contributions")
        archived = self.request.query_params.get("archived")
        if archived is not None:
            qs = qs.filter(is_archived=archived.lower() in ("1", "true", "yes"))
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        goal = self.get_object()
        goal.is_archived = True
        goal.save(update_fields=["is_archived"])
        return Response(self.get_serializer(goal).data)

    @action(detail=True, methods=["post"])
    def unarchive(self, request, pk=None):
        goal = self.get_object()
        goal.is_archived = False
        goal.save(update_fields=["is_archived"])
        return Response(self.get_serializer(goal).data)

    @action(detail=True, methods=["get", "post"], url_path="contributions")
    def contributions(self, request, pk=None):
        """Nested convenience endpoint: list a goal's contributions, or add
        one, without needing the goal id in the request body. Scoped the
        same way as the top-level /api/contributions/ endpoint."""
        goal = self.get_object()

        if request.method == "POST":
            data = request.data.copy()
            data["goal"] = goal.id
            serializer = ContributionSerializer(data=data, context={"request": request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        qs = goal.contributions.all()
        serializer = ContributionSerializer(qs, many=True, context={"request": request})
        return Response(serializer.data)


class ContributionViewSet(viewsets.ModelViewSet):
    serializer_class = ContributionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Contribution.objects.filter(goal__user=self.request.user).select_related("goal")
        goal_id = self.request.query_params.get("goal")
        if goal_id:
            qs = qs.filter(goal_id=goal_id)
        return qs

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context
