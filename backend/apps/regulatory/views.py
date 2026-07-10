from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import ComplianceCheck, Regulation, Risk
from .serializers import ComplianceCheckSerializer, RegulationSerializer, RiskSerializer


class RegulationViewSet(viewsets.ModelViewSet):
    queryset = Regulation.objects.select_related("created_by").prefetch_related(
        "compliance_checks", "risks"
    )
    serializer_class = RegulationSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["severity", "status", "jurisdiction", "is_active"]
    search_fields = ["title", "code", "description"]
    ordering_fields = ["effective_date", "review_date", "created_at"]

    @action(detail=False, methods=["get"])
    def dashboard(self, request):
        total = Regulation.objects.count()
        active = Regulation.objects.filter(status="active").count()
        overdue = sum(1 for r in Regulation.objects.all() if r.is_overdue)
        critical = Regulation.objects.filter(severity="critical").count()
        avg_compliance = ComplianceCheck.objects.filter(result="pass").count()
        total_checks = ComplianceCheck.objects.count()
        compliance_rate = (
            round((avg_compliance / total_checks) * 100, 2) if total_checks else 0
        )
        open_risks = Risk.objects.filter(status="open").count()
        return Response(
            {
                "total_regulations": total,
                "active_regulations": active,
                "overdue_reviews": overdue,
                "critical_regulations": critical,
                "compliance_rate": compliance_rate,
                "open_risks": open_risks,
            }
        )

    @action(detail=True, methods=["get"])
    def compliance_checks(self, request, pk=None):
        regulation = self.get_object()
        checks = regulation.compliance_checks.all()
        serializer = ComplianceCheckSerializer(checks, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def risks(self, request, pk=None):
        regulation = self.get_object()
        risks = regulation.risks.all()
        serializer = RiskSerializer(risks, many=True)
        return Response(serializer.data)


class ComplianceCheckViewSet(viewsets.ModelViewSet):
    queryset = ComplianceCheck.objects.select_related("regulation", "branch", "auditor")
    serializer_class = ComplianceCheckSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["regulation", "branch", "result"]
    search_fields = ["findings"]

    @action(detail=False, methods=["get"])
    def by_branch(self, request):
        branch_id = request.query_params.get("branch")
        if not branch_id:
            return Response({"error": "branch parameter required"}, status=400)
        checks = self.get_queryset().filter(branch_id=branch_id)
        serializer = self.get_serializer(checks, many=True)
        return Response(serializer.data)


class RiskViewSet(viewsets.ModelViewSet):
    queryset = Risk.objects.select_related("owner", "related_regulation")
    serializer_class = RiskSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["status", "likelihood", "impact", "related_regulation"]
    search_fields = ["title", "description"]
    ordering_fields = ["likelihood", "impact", "created_at"]

    @action(detail=False, methods=["get"])
    def heatmap(self, request):
        data = []
        for risk in Risk.objects.all():
            data.append(
                {
                    "id": str(risk.id),
                    "title": risk.title,
                    "likelihood": risk.likelihood,
                    "impact": risk.impact,
                    "score": risk.risk_score,
                    "level": risk.risk_level,
                    "status": risk.status,
                }
            )
        return Response(data)
