from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Milestone, Project, Task
from .serializers import MilestoneSerializer, ProjectSerializer, TaskSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.select_related("owner", "branch").prefetch_related(
        "tasks", "milestones"
    )
    serializer_class = ProjectSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["status", "priority", "branch", "owner"]
    search_fields = ["name", "code", "description"]
    ordering_fields = ["start_date", "end_date", "progress", "budget", "created_at"]

    @action(detail=False, methods=["get"])
    def dashboard(self, request):
        total = Project.objects.count()
        active = Project.objects.filter(status="active").count()
        completed = Project.objects.filter(status="completed").count()
        overdue = sum(1 for p in Project.objects.all() if p.is_overdue)
        total_budget = sum(p.budget for p in Project.objects.all())
        total_spent = sum(p.spent for p in Project.objects.all())
        return Response(
            {
                "total_projects": total,
                "active_projects": active,
                "completed_projects": completed,
                "overdue_projects": overdue,
                "total_budget": total_budget,
                "total_spent": total_spent,
                "budget_utilization": (
                    round((total_spent / total_budget) * 100, 2) if total_budget else 0
                ),
            }
        )

    @action(detail=True, methods=["get"])
    def tasks(self, request, pk=None):
        project = self.get_object()
        tasks = project.tasks.all()
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def milestones(self, request, pk=None):
        project = self.get_object()
        milestones = project.milestones.all()
        serializer = MilestoneSerializer(milestones, many=True)
        return Response(serializer.data)


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.select_related("project", "assignee")
    serializer_class = TaskSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["project", "status", "assignee"]
    search_fields = ["title", "description"]

    @action(detail=False, methods=["get"])
    def my_tasks(self, request):
        tasks = self.get_queryset().filter(assignee=request.user)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)


class MilestoneViewSet(viewsets.ModelViewSet):
    queryset = Milestone.objects.select_related("project")
    serializer_class = MilestoneSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["project"]
