from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.tenants.mixins import TenantScopedMixin

from .engine import run_report
from .models import ReportDefinition
from .serializers import ReportDefinitionSerializer


class ReportDefinitionViewSet(TenantScopedMixin, viewsets.ModelViewSet):
    queryset = ReportDefinition.objects.all()
    serializer_class = ReportDefinitionSerializer

    @action(detail=True, methods=["get"])
    def run(self, request, pk=None):
        defn = self.get_object()
        cols, rows = run_report(defn, request.user)
        return Response({"columns": cols, "rows": rows, "count": len(rows)})

    @action(detail=False, methods=["post"])
    def preview(self, request):
        """Run an unsaved definition from the request body."""
        defn = ReportDefinition(
            source=request.data.get("source", ""),
            columns=request.data.get("columns", []),
            filters=request.data.get("filters", []),
            group_by=request.data.get("group_by", ""),
            aggregate=request.data.get("aggregate", ""),
        )
        cols, rows = run_report(defn, request.user)
        return Response({"columns": cols, "rows": rows, "count": len(rows)})
