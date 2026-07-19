from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
from .models import Workflow, WorkflowStep, ApprovalRequest, ApprovalAction
from .serializers import (
    WorkflowSerializer, WorkflowStepSerializer,
    ApprovalRequestSerializer, ApprovalActionSerializer
)

class WorkflowViewSet(viewsets.ModelViewSet):
    queryset = Workflow.objects.all()
    serializer_class = WorkflowSerializer
    permission_classes = [IsAuthenticated]

class WorkflowStepViewSet(viewsets.ModelViewSet):
    queryset = WorkflowStep.objects.all()
    serializer_class = WorkflowStepSerializer
    permission_classes = [IsAuthenticated]

class ApprovalRequestViewSet(viewsets.ModelViewSet):
    queryset = ApprovalRequest.objects.all()
    serializer_class = ApprovalRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return ApprovalRequest.objects.filter(
            Q(requester=user) | Q(current_step__approvers=user)
        ).distinct()

    @action(detail=False, methods=['get'])
    def pending(self, request):
        requests = ApprovalRequest.objects.filter(status='pending')
        serializer = self.get_serializer(requests, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_requests(self, request):
        requests = ApprovalRequest.objects.filter(requester=request.user)
        serializer = self.get_serializer(requests, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def pending_approval(self, request):
        requests = ApprovalRequest.objects.filter(
            status='pending',
            current_step__approvers=request.user
        )
        serializer = self.get_serializer(requests, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        approval = self.get_object()
        comments = request.data.get('comments', '')

        ApprovalAction.objects.create(
            request=approval,
            step=approval.current_step,
            actor=request.user,
            action='approved',
            comments=comments
        )

        # Check if there are more steps
        next_step = WorkflowStep.objects.filter(
            workflow=approval.workflow,
            order__gt=approval.current_step.order
        ).first()

        if next_step:
            approval.current_step = next_step
            approval.save()
        else:
            approval.status = 'approved'
            approval.completed_at = timezone.now()
            approval.save()

        return Response({"status": "approved"})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        approval = self.get_object()
        comments = request.data.get('comments', '')

        ApprovalAction.objects.create(
            request=approval,
            step=approval.current_step,
            actor=request.user,
            action='rejected',
            comments=comments
        )

        approval.status = 'rejected'
        approval.completed_at = timezone.now()
        approval.save()

        return Response({"status": "rejected"})

class ApprovalActionViewSet(viewsets.ModelViewSet):
    queryset = ApprovalAction.objects.all()
    serializer_class = ApprovalActionSerializer
    permission_classes = [IsAuthenticated]
