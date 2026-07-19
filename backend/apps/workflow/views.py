from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.tenants.mixins import TenantScopedMixin

from .models import Transition, Workflow, WorkflowInstance
from .serializers import (
    TransitionSerializer, WorkflowInstanceSerializer, WorkflowSerializer,
)


class WorkflowViewSet(TenantScopedMixin, viewsets.ModelViewSet):
    """Define workflows (states) for a document type, no code."""

    queryset = Workflow.objects.prefetch_related("states", "transitions")
    serializer_class = WorkflowSerializer
    filterset_fields = ["document_type", "is_active"]
    pagination_class = None

    @action(detail=True, methods=["get"])
    def transitions(self, request, pk=None):
        wf = self.get_object()
        return Response(TransitionSerializer(wf.transitions.all(), many=True).data)


class WorkflowInstanceViewSet(TenantScopedMixin, viewsets.ReadOnlyModelViewSet):
    """Track documents moving through workflows; move them via `take`."""

    queryset = WorkflowInstance.objects.select_related("workflow", "current_state").prefetch_related("history")
    serializer_class = WorkflowInstanceSerializer
    filterset_fields = ["workflow", "current_state", "content_type", "object_id"]

    @action(detail=True, methods=["get"])
    def available(self, request, pk=None):
        """Transitions the caller may take from the current state."""
        inst = self.get_object()
        trans = inst.available_transitions(request.user)
        return Response(TransitionSerializer(trans, many=True).data)

    @action(detail=True, methods=["post"])
    def take(self, request, pk=None):
        """Move along a transition. Body: {transition: id, note}."""
        inst = self.get_object()
        tid = request.data.get("transition")
        transition = Transition.objects.filter(pk=tid, workflow=inst.workflow).first()
        if transition is None:
            return Response({"detail": "transition not found for this workflow."}, status=400)
        try:
            inst.take(transition, request.user, note=request.data.get("note", ""))
        except DjangoValidationError as exc:
            return Response({"detail": exc.messages[0]}, status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(inst).data)
