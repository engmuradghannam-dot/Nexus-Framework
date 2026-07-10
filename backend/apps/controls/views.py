"""Read-only API for the controls library, plus coverage summaries."""

from django.db.models import Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import AIAgent, FormControl, Industry, IndustryControl, MasterEntity
from .serializers import (
    AIAgentSerializer,
    FormControlSerializer,
    IndustryControlSerializer,
    IndustrySerializer,
    MasterEntitySerializer,
)


class IndustryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Industry.objects.all()
    serializer_class = IndustrySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["category"]
    search_fields = ["code", "name", "category", "description"]

    @action(detail=False, methods=["get"])
    def categories(self, request):
        """Industry counts grouped by category."""
        data = (
            Industry.objects.values("category")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        return Response(list(data))


class IndustryControlViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = IndustryControl.objects.all()
    serializer_class = IndustryControlSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["industry", "module", "required", "compliance"]
    search_fields = ["control_id", "control_name", "description", "ai_agent"]


class AIAgentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AIAgent.objects.all()
    serializer_class = AIAgentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["industry"]
    search_fields = ["name", "responsibility", "database_entity"]


class MasterEntityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MasterEntity.objects.all()
    serializer_class = MasterEntitySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "entity_type", "usage"]


class FormControlViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FormControl.objects.all()
    serializer_class = FormControlSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["form_name", "status", "priority", "input_type"]
    search_fields = ["form_name", "input_name", "input_type"]

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """Overall coverage summary across all form controls."""
        qs = FormControl.objects.all()
        total = qs.count()
        present = qs.filter(status=FormControl.STATUS_PRESENT).count()
        missing = qs.filter(status=FormControl.STATUS_MISSING).count()
        planned = qs.filter(status=FormControl.STATUS_PLANNED).count()
        coverage = round((present / total) * 100, 1) if total else 0.0
        return Response(
            {
                "total": total,
                "present": present,
                "missing": missing,
                "planned": planned,
                "coverage_percent": coverage,
                "high_priority_missing": qs.filter(
                    status=FormControl.STATUS_MISSING, priority="High"
                ).count(),
            }
        )

    @action(detail=False, methods=["get"])
    def by_form(self, request):
        """Per-form coverage breakdown."""
        data = (
            FormControl.objects.values("form_name")
            .annotate(
                total=Count("id"),
                present=Count("id", filter=Q(status=FormControl.STATUS_PRESENT)),
                missing=Count("id", filter=Q(status=FormControl.STATUS_MISSING)),
                planned=Count("id", filter=Q(status=FormControl.STATUS_PLANNED)),
            )
            .order_by("form_name")
        )
        result = []
        for row in data:
            total = row["total"] or 1
            row["coverage_percent"] = round((row["present"] / total) * 100, 1)
            result.append(row)
        return Response(result)
