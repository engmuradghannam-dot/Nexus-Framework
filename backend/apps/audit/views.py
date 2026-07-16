from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets

from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """AuditLog has no company/tenant FK (only the acting `user`), so there's
    no way to scope it per-company yet — a non-superuser can only read
    their own audit trail until that's added."""

    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["module", "action", "user_email"]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if getattr(user, "is_superuser", False):
            return qs
        return qs.filter(user=user)
