from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from apps.core.mixins import CompanyScopedMixin

from .models import ComplianceCheck, Regulation, Risk
from .serializers import ComplianceCheckSerializer, RegulationSerializer, RiskSerializer


def _scoped_compliance_checks(user):
    qs = ComplianceCheck.objects.all()
    if getattr(user, "is_superuser", False):
        return qs
    companies = getattr(user, "managed_companies", None)
    if companies is None:
        return qs.none()
    return qs.filter(branch__company__in=companies.all())


def _scoped_risks(user):
    if getattr(user, "is_superuser", False):
        return Risk.objects.all()
    return Risk.objects.filter(owner=user)


class RegulationViewSet(viewsets.ModelViewSet):
    """Regulations are a shared reference catalog (jurisdiction law text,
    no per-company ownership) — reading is open to any authenticated user,
    but only a superuser may add/edit/retire an entry."""

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

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAdminUser()]
        return super().get_permissions()

    @action(detail=False, methods=["get"])
    def dashboard(self, request):
        checks = _scoped_compliance_checks(request.user)
        risks = _scoped_risks(request.user)
        total = Regulation.objects.count()
        active = Regulation.objects.filter(status="active").count()
        overdue = sum(1 for r in Regulation.objects.all() if r.is_overdue)
        critical = Regulation.objects.filter(severity="critical").count()
        avg_compliance = checks.filter(result="pass").count()
        total_checks = checks.count()
        compliance_rate = (
            round((avg_compliance / total_checks) * 100, 2) if total_checks else 0
        )
        open_risks = risks.filter(status="open").count()
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
        checks = _scoped_compliance_checks(request.user).filter(regulation=regulation)
        serializer = ComplianceCheckSerializer(checks, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def risks(self, request, pk=None):
        regulation = self.get_object()
        risks = _scoped_risks(request.user).filter(related_regulation=regulation)
        serializer = RiskSerializer(risks, many=True)
        return Response(serializer.data)


class ComplianceCheckViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = ComplianceCheck.objects.select_related("regulation", "branch", "auditor")
    serializer_class = ComplianceCheckSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["regulation", "branch", "result"]
    search_fields = ["findings"]
    company_field = "branch__company"

    @action(detail=False, methods=["get"])
    def by_branch(self, request):
        branch_id = request.query_params.get("branch")
        if not branch_id:
            return Response({"error": "branch parameter required"}, status=400)
        checks = self.get_queryset().filter(branch_id=branch_id)
        serializer = self.get_serializer(checks, many=True)
        return Response(serializer.data)


class RiskViewSet(viewsets.ModelViewSet):
    """Risks have no company FK, only an `owner` (the user who logged it) —
    a non-superuser only sees/manages risks they own."""

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

    def get_queryset(self):
        return _scoped_risks(self.request.user).select_related(
            "owner", "related_regulation"
        )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=False, methods=["get"])
    def heatmap(self, request):
        data = []
        for risk in self.get_queryset():
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
