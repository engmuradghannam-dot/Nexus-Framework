from django.core.exceptions import ValidationError as DjangoValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response

from apps.core.mixins import CompanyScopedMixin

from .models import (  # noqa: F401
    EmployeeTermination,
    EndOfServiceBand,
    EndOfServicePolicy,
    HRPolicy,
    LeaveEntitlement,
)
from .models import Department, Employee, LeaveRequest, Payroll, Team
from .serializers import (  # noqa: F401
    EmployeeTerminationSerializer,
    EndOfServiceBandSerializer,
    EndOfServicePolicySerializer,
    HRPolicySerializer,
    LeaveEntitlementSerializer,
)
from .serializers import (
    DepartmentSerializer,
    EmployeeSerializer,
    LeaveRequestSerializer,
    PayrollSerializer,
    TeamSerializer,
)


class EmployeeViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ["first_name", "last_name", "employee_id", "email", "national_id"]
    filterset_fields = ["department", "status", "company"]
    company_field = "company"

    @action(detail=True, methods=["get"])
    def end_of_service(self, request, pk=None):
        """HR-RULE-003: the benefit as HR's own bands compute it.

        `resigned=true` applies each band's resignation fraction.
        """
        employee = self.get_object()
        resigned = str(request.query_params.get("resigned", "")).lower() in ("1", "true", "yes")
        try:
            result = employee.end_of_service_benefit(resigned=resigned)
        except DjangoValidationError as exc:
            return Response({"detail": exc.messages[0]}, status=400)
        return Response(result)

    @action(detail=True, methods=["get"])
    def leave_entitlement(self, request, pk=None):
        """HR-RULE-001: entitlement and monthly accrual at current tenure."""
        employee = self.get_object()
        return Response({
            "tenure_years": str(employee.tenure_years()),
            "employment_type": employee.employment_type,
            "days_per_year": str(employee.leave_entitlement_days()),
            "accrual_per_month": str(employee.monthly_leave_accrual()),
        })


class DepartmentViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    filter_backends = [SearchFilter]
    search_fields = ["name"]
    company_field = "company"


class TeamViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ["name"]
    filterset_fields = ["lead"]
    company_field = "company"


class LeaveRequestViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = LeaveRequest.objects.all()
    serializer_class = LeaveRequestSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["employee", "status", "leave_type", "year"]
    company_field = "employee__company"


class PayrollViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = Payroll.objects.all()
    serializer_class = PayrollSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["employee", "status"]
    company_field = "employee__company"


class EmployeeTerminationViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    """HR-CTRL-004: the termination log."""

    queryset = EmployeeTermination.objects.select_related("employee")
    serializer_class = EmployeeTerminationSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["employee", "status", "reason"]
    company_field = "employee__company"

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(requested_by=user)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        termination = self.get_object()
        try:
            ok, message = termination.approve()
        except DjangoValidationError as exc:
            return Response({"detail": exc.messages[0]}, status=400)
        return Response({"success": ok, "message": message,
                         "employee_status": termination.employee.status})


class HRPolicyViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    """The parameters HR owns: probation length, overtime multipliers, default
    leave. Previously hardcoded constants."""

    queryset = HRPolicy.objects.select_related("company")
    serializer_class = HRPolicySerializer
    filterset_fields = ["company"]
    company_field = "company"


class LeaveEntitlementViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    """HR-RULE-001: HR enters the accrual rules here."""

    queryset = LeaveEntitlement.objects.select_related("company")
    serializer_class = LeaveEntitlementSerializer
    filterset_fields = ["company", "employment_type", "is_active"]
    company_field = "company"


class EndOfServicePolicyViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    """HR-RULE-003: HR enters the tenure bands here."""

    queryset = EndOfServicePolicy.objects.select_related("company").prefetch_related("bands")
    serializer_class = EndOfServicePolicySerializer
    filterset_fields = ["company"]
    company_field = "company"


class EndOfServiceBandViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = EndOfServiceBand.objects.select_related("policy")
    serializer_class = EndOfServiceBandSerializer
    filterset_fields = ["policy"]
    company_field = "policy__company"
