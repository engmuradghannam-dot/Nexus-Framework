from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from nexus.apps.api_infra.scoping import CompanyScopedViewSet
from .models import Project, Task, Milestone
from .serializers import ProjectSerializer, TaskSerializer, MilestoneSerializer


class ProjectViewSet(CompanyScopedViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    company_field = "company"

    @action(detail=False, methods=['get'])
    def by_company(self, request):
        return Response(self.get_serializer(self.get_queryset(), many=True).data)

    @action(detail=False, methods=['get'])
    def by_status(self, request):
        status_filter = request.query_params.get('status')
        if not status_filter:
            return Response({"error": "status required"}, status=status.HTTP_400_BAD_REQUEST)
        projects = self.get_queryset().filter(status=status_filter)
        return Response(self.get_serializer(projects, many=True).data)


class TaskViewSet(CompanyScopedViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    company_field = "project__company"

    @action(detail=False, methods=['get'])
    def by_project(self, request):
        project_id = request.query_params.get('project_id')
        if not project_id:
            return Response({"error": "project_id required"}, status=status.HTTP_400_BAD_REQUEST)
        tasks = self.get_queryset().filter(project_id=project_id)
        return Response(self.get_serializer(tasks, many=True).data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        task = self.get_object()
        task.completed = True
        task.save()
        return Response({"status": "task completed"})

    @action(detail=True, methods=['get'])
    def gantt_data(self, request, pk=None):
        project = self.get_object()
        data = [{
            'id': t.id, 'name': t.name, 'start': t.start_date, 'end': t.end_date,
            'progress': 100 if t.completed else 0, 'dependencies': []
        } for t in project.tasks.all()]
        return Response(data)

    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        project = self.get_object()
        return Response({
            'milestones': [{'name': m.name, 'date': m.target_date} for m in project.milestones.all()],
            'tasks': [{'name': t.name, 'start': t.start_date, 'end': t.end_date} for t in project.tasks.all()],
        })

    @action(detail=True, methods=['get'])
    def resource_allocation(self, request, pk=None):
        project = self.get_object()
        allocation = {}
        for task in project.tasks.all():
            if task.assigned_to:
                allocation[task.assigned_to.username] = allocation.get(task.assigned_to.username, 0) + 1
        return Response(allocation)

    @action(detail=True, methods=['get'])
    def budget_vs_actual(self, request, pk=None):
        project = self.get_object()
        total_budget = project.budget
        actual = sum(t.estimated_hours * 50 for t in project.tasks.all() if t.estimated_hours)
        return Response({
            'budget': total_budget, 'actual': actual,
            'variance': total_budget - actual,
            'percentage': (actual / total_budget * 100) if total_budget else 0,
        })


class MilestoneViewSet(CompanyScopedViewSet):
    queryset = Milestone.objects.all()
    serializer_class = MilestoneSerializer
    company_field = "project__company"
