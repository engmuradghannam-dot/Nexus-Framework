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


    @action(detail=True, methods=['post'])
    def conditional_check(self, request, pk=None):
        approval = self.get_object()
        step = approval.current_step

        if step.condition_field and step.condition_value:
            # Check condition on content_object
            obj = approval.content_object
            field_value = getattr(obj, step.condition_field, None)
            condition_met = str(field_value) == step.condition_value

            return Response({
                "condition_met": condition_met,
                "field": step.condition_field,
                "expected": step.condition_value,
                "actual": field_value
            })
        return Response({"condition_met": True, "reason": "no condition set"})

    @action(detail=True, methods=['post'])
    def auto_escalate(self, request, pk=None):
        approval = self.get_object()
        step = approval.current_step

        if step.auto_approve_after > 0:
            from datetime import timedelta
            deadline = approval.created_at + timedelta(hours=step.auto_approve_after)
            if timezone.now() > deadline:
                ApprovalAction.objects.create(
                    request=approval,
                    step=step,
                    actor=request.user,
                    action='approved',
                    comments='Auto-approved after deadline'
                )
                approval.status = 'approved'
                approval.completed_at = timezone.now()
                approval.save()
                return Response({"status": "auto-approved"})
            return Response({"status": "pending", "deadline": deadline})
        return Response({"error": "auto-escalation not configured"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def delegate(self, request, pk=None):
        approval = self.get_object()
        delegate_to_id = request.data.get('user_id')
        if delegate_to_id:
            from django.contrib.auth.models import User
            try:
                delegate = User.objects.get(id=delegate_to_id)
                ApprovalAction.objects.create(
                    request=approval,
                    step=approval.current_step,
                    actor=request.user,
                    action='delegated',
                    comments=f'Delegated to {delegate.username}'
                )
                approval.current_step.approvers.add(delegate)
                return Response({"status": "delegated", "to": delegate.username})
            except User.DoesNotExist:
                return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"error": "user_id required"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def send_reminder(self, request):
        request_id = request.data.get('request_id')
        if request_id:
            approval = ApprovalRequest.objects.get(id=request_id)
            approvers = approval.current_step.approvers.all()
            return Response({
                "status": "reminders sent",
                "approvers": [u.username for u in approvers],
                "request": approval.title
            })
        return Response({"error": "request_id required"}, status=status.HTTP_400_BAD_REQUEST)


class ApprovalActionViewSet(viewsets.ModelViewSet):
    queryset = ApprovalAction.objects.all()
    serializer_class = ApprovalActionSerializer
    permission_classes = [IsAuthenticated]
