"""
Industry Vertical Control Views
Industry Vertical is the PARENT - it controls what modules/features appear.
"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Company, IndustryVertical, Metric, Sector, VerticalTemplate
from .serializers import (
    CompanyListSerializer,
    CompanySerializer,
    IndustryVerticalSerializer,
    MetricSerializer,
    SectorSerializer,
    VerticalTemplateSerializer,
)


class IndustryVerticalViewSet(viewsets.ModelViewSet):
    """
    Industry Vertical Control Center
    - Super Admin creates/selects the vertical
    - Vertical determines what modules/features are available
    """

    queryset = IndustryVertical.objects.prefetch_related("companies", "sectors")
    serializer_class = IndustryVerticalSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["is_active", "default_currency", "multi_branch_enabled"]
    search_fields = ["name", "code", "description"]

    @action(detail=True, methods=["get"])
    def modules(self, request, pk=None):
        """Get available modules for this vertical"""
        vertical = self.get_object()
        return Response(
            {
                "vertical_id": str(vertical.id),
                "vertical_name": vertical.name,
                "modules_enabled": vertical.modules_enabled,
                "features_config": vertical.features_config,
                "report_templates": vertical.report_templates,
            }
        )

    @action(detail=True, methods=["get"])
    def companies(self, request, pk=None):
        """Get all companies under this vertical"""
        vertical = self.get_object()
        companies = vertical.companies.all()
        serializer = CompanyListSerializer(companies, many=True)
        return Response(
            {
                "vertical": vertical.name,
                "count": companies.count(),
                "companies": serializer.data,
            }
        )

    @action(detail=True, methods=["post"])
    def clone_from_template(self, request, pk=None):
        """Clone configuration from a template"""
        vertical = self.get_object()
        template_id = request.data.get("template_id")

        try:
            template = VerticalTemplate.objects.get(id=template_id)
        except VerticalTemplate.DoesNotExist:
            return Response(
                {"error": "Template not found"}, status=status.HTTP_404_NOT_FOUND
            )

        vertical.modules_enabled = template.default_modules
        vertical.features_config = template.default_features
        vertical.report_templates = template.default_reports
        vertical.compliance_frameworks = template.default_compliance
        vertical.save()

        serializer = self.get_serializer(vertical)
        return Response(
            {
                "message": f"Cloned from template: {template.name}",
                "vertical": serializer.data,
            }
        )

    @action(detail=False, methods=["get"])
    def active_verticals(self, request):
        """Get only active verticals with summary"""
        verticals = self.get_queryset().filter(is_active=True)
        data = []
        for v in verticals:
            data.append(
                {
                    "id": str(v.id),
                    "name": v.name,
                    "code": v.code,
                    "company_count": v.companies.count(),
                    "modules": v.modules_enabled,
                    "multi_branch": v.multi_branch_enabled,
                    "multi_warehouse": v.multi_warehouse_enabled,
                }
            )
        return Response(data)


class VerticalTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Pre-configured templates for Industry Verticals.
    Super Admin uses these to quickly set up new verticals.
    """

    queryset = VerticalTemplate.objects.filter(is_active=True)
    serializer_class = VerticalTemplateSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["vertical_type"]
    search_fields = ["name", "description"]

    @action(detail=True, methods=["get"])
    def preview(self, request, pk=None):
        """Preview what a vertical would look like using this template"""
        template = self.get_object()
        return Response(
            {
                "template_name": template.name,
                "vertical_type": template.vertical_type,
                "modules": template.default_modules,
                "features": template.default_features,
                "reports": template.default_reports,
                "compliance": template.default_compliance,
            }
        )


class CompanyViewSet(viewsets.ModelViewSet):
    """
    Company - Child of Industry Vertical.
    All modules/features are derived from the parent vertical.
    """

    queryset = Company.objects.select_related("industry_vertical").prefetch_related(
        "metrics"
    )
    serializer_class = CompanySerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["industry_vertical", "is_active", "multi_branch_enabled"]
    search_fields = ["name", "ticker", "headquarters"]
    ordering_fields = ["market_cap", "revenue", "employees", "created_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return CompanyListSerializer
        return CompanySerializer

    @action(detail=True, methods=["get"])
    def modules(self, request, pk=None):
        """Get effective modules for this company"""
        company = self.get_object()
        return Response(
            {
                "company": company.name,
                "vertical": company.industry_vertical.name,
                "effective_modules": company.effective_modules,
                "effective_features": company.effective_features,
            }
        )

    @action(detail=True, methods=["get"])
    def reports(self, request, pk=None):
        """Get available reports for this company"""
        company = self.get_object()
        return Response(
            {
                "company": company.name,
                "available_reports": company.available_reports,
            }
        )

    @action(detail=True, methods=["get"])
    def metrics(self, request, pk=None):
        company = self.get_object()
        metrics = company.metrics.all()
        serializer = MetricSerializer(metrics, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def by_vertical(self, request):
        """Group companies by their Industry Vertical"""
        vertical_id = request.query_params.get("vertical_id")
        if vertical_id:
            companies = self.get_queryset().filter(industry_vertical_id=vertical_id)
        else:
            companies = self.get_queryset()

        serializer = CompanyListSerializer(companies, many=True)
        return Response({"count": companies.count(), "companies": serializer.data})

    @action(detail=False, methods=["get"])
    def leaderboard(self, request):
        """Top companies by market cap"""
        top = self.get_queryset().order_by("-market_cap")[:10]
        serializer = CompanyListSerializer(top, many=True)
        return Response(serializer.data)


class SectorViewSet(viewsets.ModelViewSet):
    queryset = Sector.objects.select_related("industry_vertical").prefetch_related(
        "sub_sectors"
    )
    serializer_class = SectorSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["industry_vertical", "is_active", "parent_sector"]
    search_fields = ["name", "code"]


class MetricViewSet(viewsets.ModelViewSet):
    queryset = Metric.objects.select_related("company")
    serializer_class = MetricSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["company", "metric_type", "period"]
    search_fields = ["name", "period"]
