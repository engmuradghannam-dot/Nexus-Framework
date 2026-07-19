from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Count

from nexus.apps.api_infra.scoping import CompanyScopedViewSet, user_company_ids
from .models import (
    Employee, Attendance, LeaveType, LeaveRequest,
    SalaryStructure, EmployeeSalary, PayrollRun, Payslip
)
from .serializers import (
    EmployeeSerializer, AttendanceSerializer, LeaveTypeSerializer,
    LeaveRequestSerializer, SalaryStructureSerializer, EmployeeSalarySerializer,
    PayrollRunSerializer, PayslipSerializer
)


class EmployeeViewSet(CompanyScopedViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    company_field = "company"

    @action(detail=False, methods=['get'])
    def by_company(self, request):
        return Response(self.get_serializer(self.get_queryset(), many=True).data)

    @action(detail=False, methods=['get'])
    def by_department(self, request):
        dept_id = request.query_params.get('department_id')
        if not dept_id:
            return Response({"error": "department_id required"}, status=status.HTTP_400_BAD_REQUEST)
        emps = self.get_queryset().filter(department_id=dept_id)
        return Response(self.get_serializer(emps, many=True).data)

    @action(detail=False, methods=['get'])
    def by_branch(self, request):
        branch_id = request.query_params.get('branch_id')
        if not branch_id:
            return Response({"error": "branch_id required"}, status=status.HTTP_400_BAD_REQUEST)
        emps = self.get_queryset().filter(branch_id=branch_id)
        return Response(self.get_serializer(emps, many=True).data)


class AttendanceViewSet(CompanyScopedViewSet):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    company_field = "employee__company"

    @action(detail=False, methods=['get'])
    def by_employee(self, request):
        employee_id = request.query_params.get('employee_id')
        if not employee_id:
            return Response({"error": "employee_id required"}, status=status.HTTP_400_BAD_REQUEST)
        att = self.get_queryset().filter(employee_id=employee_id)
        return Response(self.get_serializer(att, many=True).data)

    @action(detail=False, methods=['get'])
    def today(self, request):
        att = self.get_queryset().filter(date=timezone.now().date())
        return Response(self.get_serializer(att, many=True).data)

    @action(detail=False, methods=['post'])
    def bulk_check_in(self, request):
        employee_ids = request.data.get('employee_ids', [])
        allowed = user_company_ids(request.user)
        emp_qs = Employee.objects.all()
        if allowed is not None:
            emp_qs = emp_qs.filter(company_id__in=allowed) if allowed else emp_qs.none()
        valid_ids = set(emp_qs.filter(id__in=employee_ids).values_list('id', flat=True))
        today = timezone.now().date()
        now = timezone.now().time()
        created = []
        for emp_id in valid_ids:
            attendance, _ = Attendance.objects.get_or_create(
                employee_id=emp_id, date=today,
                defaults={'check_in': now, 'status': 'present'})
            created.append(attendance)
        return Response(self.get_serializer(created, many=True).data)

    @action(detail=False, methods=['get'])
    def attendance_report(self, request):
        month = request.query_params.get('month')
        year = request.query_params.get('year')
        attendances = self.get_queryset()
        if month and year:
            attendances = attendances.filter(date__year=year, date__month=month)
        report = list(attendances.values('status').annotate(count=Count('id')))
        total = attendances.count()
        present = next((r['count'] for r in report if r['status'] == 'present'), 0)
        return Response({
            "period": f"{year}-{month}" if month and year else "all",
            "total_records": total, "breakdown": report,
            "present_rate": present / total * 100 if total else 0,
        })

    @action(detail=True, methods=['get'])
    def leave_balance(self, request, pk=None):
        employee = self.get_object()
        balances = []
        for lt in LeaveType.objects.all():
            used = LeaveRequest.objects.filter(
                employee=employee, leave_type=lt, status='approved').count()
            balances.append({"leave_type": lt.name, "entitled": lt.days_per_year,
                             "used": used, "remaining": lt.days_per_year - used})
        return Response({"employee": employee.full_name, "balances": balances})

    @action(detail=False, methods=['get'])
    def overtime_tracking(self, request):
        month = request.query_params.get('month')
        year = request.query_params.get('year')
        attendances = self.get_queryset().filter(status='present')
        if month and year:
            attendances = attendances.filter(date__year=year, date__month=month)

        allowed = user_company_ids(request.user)
        emps = Employee.objects.filter(status='active')
        if allowed is not None:
            emps = emps.filter(company_id__in=allowed) if allowed else emps.none()

        from datetime import datetime
        overtime_data = []
        for emp in emps:
            total_hours = 0
            for att in attendances.filter(employee=emp):
                if att.check_in and att.check_out:
                    hours = (datetime.combine(att.date, att.check_out) -
                             datetime.combine(att.date, att.check_in)).total_seconds() / 3600
                    total_hours += max(0, hours - 8)
            overtime_data.append({"employee": emp.full_name,
                                  "overtime_hours": round(total_hours, 2)})
        return Response({"month": month, "year": year, "overtime": overtime_data})


class LeaveTypeViewSet(viewsets.ModelViewSet):
    """Shared lookup — no company FK."""
    queryset = LeaveType.objects.all()
    serializer_class = LeaveTypeSerializer
    permission_classes = [IsAuthenticated]


class LeaveRequestViewSet(CompanyScopedViewSet):
    queryset = LeaveRequest.objects.all()
    serializer_class = LeaveRequestSerializer
    company_field = "employee__company"

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        leave = self.get_object()
        leave.status = 'approved'
        leave.approved_by = getattr(request.user, 'employee', None)
        leave.approved_at = timezone.now()
        leave.save()
        return Response({"status": "approved"})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        leave = self.get_object()
        leave.status = 'rejected'
        leave.approved_by = getattr(request.user, 'employee', None)
        leave.approved_at = timezone.now()
        leave.save()
        return Response({"status": "rejected"})


class SalaryStructureViewSet(viewsets.ModelViewSet):
    # MODEL GAP: SalaryStructure has no company FK, so it cannot be tenant-scoped.
    # Add a company FK to scope salary bands per tenant.
    queryset = SalaryStructure.objects.all()
    serializer_class = SalaryStructureSerializer
    permission_classes = [IsAuthenticated]


class EmployeeSalaryViewSet(CompanyScopedViewSet):
    queryset = EmployeeSalary.objects.all()
    serializer_class = EmployeeSalarySerializer
    company_field = "employee__company"


class PayrollRunViewSet(viewsets.ModelViewSet):
    # MODEL GAP: PayrollRun has no company FK — cannot be tenant-scoped as-is.
    # generate_payslips below is limited to the caller's employees as a stopgap.
    queryset = PayrollRun.objects.all()
    serializer_class = PayrollRunSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def generate_payslips(self, request, pk=None):
        payroll = self.get_object()
        allowed = user_company_ids(request.user)
        employees = Employee.objects.filter(status='active')
        if allowed is not None:
            employees = employees.filter(company_id__in=allowed) if allowed else employees.none()

        payslips = []
        for emp in employees:
            salary = getattr(emp, 'salary_structure', None)
            if not salary:
                continue
            s = salary.salary_structure
            basic = s.basic_salary
            allowances = s.housing_allowance + s.transport_allowance + s.other_allowances
            deductions = s.tax_deduction + s.insurance_deduction + s.other_deductions
            payslip, _ = Payslip.objects.get_or_create(
                payroll_run=payroll, employee=emp,
                defaults={'basic_salary': basic, 'allowances': allowances,
                          'deductions': deductions, 'net_salary': basic + allowances - deductions})
            payslips.append(payslip)

        payroll.status = 'completed'
        payroll.save(update_fields=['status'])
        return Response(PayslipSerializer(payslips, many=True).data)


class PayslipViewSet(CompanyScopedViewSet):
    queryset = Payslip.objects.all()
    serializer_class = PayslipSerializer
    company_field = "employee__company"

    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        payslip = self.get_object()
        payslip.status = 'paid'
        payslip.paid_at = timezone.now()
        payslip.save()
        return Response({"status": "paid"})
