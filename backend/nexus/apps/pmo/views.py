from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Project, Task, Milestone
from .serializers import ProjectSerializer, TaskSerializer, MilestoneSerializer

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def by_company(self, request):
        company_id = request.query_params.get('company_id')
        if company_id:
            projects = Project.objects.filter(company_id=company_id)
            serializer = self.get_serializer(projects, many=True)
            return Response(serializer.data)
        return Response({"error": "company_id required"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def by_status(self, request):
        status_filter = request.query_params.get('status')
        if status_filter:
            projects = Project.objects.filter(status=status_filter)
            serializer = self.get_serializer(projects, many=True)
            return Response(serializer.data)
        return Response({"error": "status required"}, status=status.HTTP_400_BAD_REQUEST)

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def by_project(self, request):
        project_id = request.query_params.get('project_id')
        if project_id:
            tasks = Task.objects.filter(project_id=project_id)
            serializer = self.get_serializer(tasks, many=True)
            return Response(serializer.data)
        return Response({"error": "project_id required"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        task = self.get_object()
        task.completed = True
        task.save()
        return Response({"status": "task completed"})

class MilestoneViewSet(viewsets.ModelViewSet):
    queryset = Milestone.objects.all()
    serializer_class = MilestoneSerializer
    permission_classes = [IsAuthenticated]
