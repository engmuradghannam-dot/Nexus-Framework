from django.core.exceptions import ValidationError as DjangoValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response

from apps.core.mixins import CompanyScopedMixin

from .models import EmployeeTermination  # noqa: F401
from .models import Department, Employee, LeaveRequest, Payroll, Team
from .serializers import EmployeeTerminationSerializer  # noqa: F401
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
