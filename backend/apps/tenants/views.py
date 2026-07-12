from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Tenant
from .serializers import TenantSerializer


class TenantViewSet(viewsets.ModelViewSet):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_superuser:
            return qs
        t = getattr(user, "tenant", None)
        return qs.filter(id=t.id) if t else qs.none()

    @action(detail=False, methods=["get"])
    def current(self, request):
        """The tenant the current user belongs to."""
        t = getattr(request.user, "tenant", None)
        if t is None:
            return Response({"tenant": None, "is_superuser": request.user.is_superuser})
        return Response({"tenant": TenantSerializer(t).data, "is_superuser": request.user.is_superuser})
