from rest_framework import viewsets
from rest_framework.filters import SearchFilter
from .models import Workflow, WorkflowState, WorkflowTransition
from .serializers import WorkflowSerializer, WorkflowStateSerializer, WorkflowTransitionSerializer

class WorkflowViewSet(viewsets.ModelViewSet):
    queryset = Workflow.objects.all()
    serializer_class = WorkflowSerializer
    filter_backends = [SearchFilter]
    search_fields = ['name', 'document_type']
