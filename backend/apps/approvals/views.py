from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.tenants.mixins import TenantScopedMixin

from .models import ApprovalRequest, ReleaseStrategy
from .serializers import ApprovalRequestSerializer, ReleaseStrategySerializer


class ReleaseStrategyViewSet(TenantScopedMixin, viewsets.ModelViewSet):
    """Define which documents, above which amounts, route through which chain."""

    queryset = ReleaseStrategy.objects.prefetch_related("levels__role")
    serializer_class = ReleaseStrategySerializer
    filterset_fields = ["document_type", "is_active"]
    pagination_class = None


class ApprovalRequestViewSet(TenantScopedMixin, viewsets.ReadOnlyModelViewSet):
    """Track documents under approval and act on the current level.

    Read-only for creation (requests are opened by the documents they gate, via
    ApprovalRequest.open_for), but exposes an `act` action to approve or reject
    the current level, and a `pending` list of what awaits the caller.
    """

    queryset = ApprovalRequest.objects.select_related("strategy").prefetch_related("steps__level__role")
    serializer_class = ApprovalRequestSerializer
    filterset_fields = ["document_type", "status"]

    @action(detail=True, methods=["post"])
    def act(self, request, pk=None):
        """Approve or reject the current level. Body: {approve: bool, comment}."""
        approval = self.get_object()
        approve = bool(request.data.get("approve", True))
        comment = request.data.get("comment", "")
        try:
            approval.act(request.user, approve=approve, comment=comment)
        except DjangoValidationError as exc:
            return Response({"detail": exc.messages[0]}, status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(approval).data)

    @action(detail=False, methods=["get"])
    def pending(self, request):
        """Requests whose current level is one the caller can release."""
        from apps.rbac.models import RoleAssignment

        roles = set(
            RoleAssignment.objects.filter(user=request.user).values_list("role_id", flat=True)
        )
        out = []
        for req in self.get_queryset().filter(status="pending"):
            step = req.current_step
            if step and step.level.role_id in roles and req.requested_by_id != request.user.pk:
                out.append(req)
        return Response(self.get_serializer(out, many=True).data)
