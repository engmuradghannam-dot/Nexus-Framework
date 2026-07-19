from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
from .models import Employee, Attendance, LeaveType, LeaveRequest, SalaryStructure, EmployeeSalary, PayrollRun, Payslip
from .serializers import (
    EmployeeSerializer, AttendanceSerializer, LeaveTypeSerializer,
    LeaveRequestSerializer, SalaryStructureSerializer, EmployeeSalarySerializer,
    PayrollRunSerializer, PayslipSerializer
)

class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def by_company(self, request):
        company_id = request.query_params.get('company_id')
        if company_id:
            employees = Employee.objects.filter(company_id=company_id)
            serializer = self.get_serializer(employees, many=True)
            return Response(serializer.data)
        return Response({"error": "company_id required"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def by_department(self, request):
        dept_id = request.query_params.get('department_id')
        if dept_id:
            employees = Employee.objects.filter(department_id=dept_id)
            serializer = self.get_serializer(employees, many=True)
            return Response(serializer.data)
        return Response({"error": "department_id required"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def by_branch(self, request):
        branch_id = request.query_params.get('branch_id')
        if branch_id:
            employees = Employee.objects.filter(branch_id=branch_id)
            serializer = self.get_serializer(employees, many=True)
            return Response(serializer.data)
        return Response({"error": "branch_id required"}, status=status.HTTP_400_BAD_REQUEST)

class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def by_employee(self, request):
        employee_id = request.query_params.get('employee_id')
        if employee_id:
            attendances = Attendance.objects.filter(employee_id=employee_id)
            serializer = self.get_serializer(attendances, many=True)
            return Response(serializer.data)
        return Response({"error": "employee_id required"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def today(self, request):
        today = timezone.now().date()
        attendances = Attendance.objects.filter(date=today)
        serializer = self.get_serializer(attendances, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def bulk_check_in(self, request):
        employee_ids = request.data.get('employee_ids', [])
        today = timezone.now().date()
        now = timezone.now().time()

        created = []
        for emp_id in employee_ids:
            attendance, _ = Attendance.objects.get_or_create(
                employee_id=emp_id,
                date=today,
                defaults={'check_in': now, 'status': 'present'}
            )
            created.append(attendance)

        serializer = self.get_serializer(created, many=True)
        return Response(serializer.data)

class LeaveTypeViewSet(viewsets.ModelViewSet):
    queryset = LeaveType.objects.all()
    serializer_class = LeaveTypeSerializer
    permission_classes = [IsAuthenticated]

class LeaveRequestViewSet(viewsets.ModelViewSet):
    queryset = LeaveRequest.objects.all()
    serializer_class = LeaveRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'employee'):
            return LeaveRequest.objects.filter(employee=user.employee)
        return LeaveRequest.objects.all()

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
    queryset = SalaryStructure.objects.all()
    serializer_class = SalaryStructureSerializer
    permission_classes = [IsAuthenticated]

class EmployeeSalaryViewSet(viewsets.ModelViewSet):
    queryset = EmployeeSalary.objects.all()
    serializer_class = EmployeeSalarySerializer
    permission_classes = [IsAuthenticated]

class PayrollRunViewSet(viewsets.ModelViewSet):
    queryset = PayrollRun.objects.all()
    serializer_class = PayrollRunSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def generate_payslips(self, request, pk=None):
        payroll = self.get_object()
        employees = Employee.objects.filter(status='active')

        payslips = []
        for emp in employees:
            salary = getattr(emp, 'salary_structure', None)
            if salary:
                basic = salary.salary_structure.basic_salary
                allowances = (salary.salary_structure.housing_allowance +
                            salary.salary_structure.transport_allowance +
                            salary.salary_structure.other_allowances)
                deductions = (salary.salary_structure.tax_deduction +
                            salary.salary_structure.insurance_deduction +
                            salary.salary_structure.other_deductions)
                net = basic + allowances - deductions

                payslip, _ = Payslip.objects.get_or_create(
                    payroll_run=payroll,
                    employee=emp,
                    defaults={
                        'basic_salary': basic,
                        'allowances': allowances,
                        'deductions': deductions,
                        'net_salary': net
                    }
                )
                payslips.append(payslip)

        payroll.status = 'completed'
        payroll.save()

        serializer = PayslipSerializer(payslips, many=True)
        return Response(serializer.data)

class PayslipViewSet(viewsets.ModelViewSet):
    queryset = Payslip.objects.all()
    serializer_class = PayslipSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        payslip = self.get_object()
        payslip.status = 'paid'
        payslip.paid_at = timezone.now()
        payslip.save()
        return Response({"status": "paid"})
