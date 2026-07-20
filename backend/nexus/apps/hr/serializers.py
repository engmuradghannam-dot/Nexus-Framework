from django.utils import timezone
from rest_framework import serializers
from .models import Employee, Attendance, LeaveType, LeaveRequest, SalaryStructure, EmployeeSalary, PayrollRun, Payslip

class EmployeeSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    manager_name = serializers.CharField(source='manager.full_name', read_only=True)
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Employee
        fields = '__all__'
        read_only_fields = ['employee_id']

    def validate(self, attrs):
        manager = attrs.get('manager', getattr(self.instance, 'manager', None))
        if self.instance and manager and manager.pk == self.instance.pk:
            raise serializers.ValidationError('Employee cannot be their own manager')
        hire_date = attrs.get('hire_date', getattr(self.instance, 'hire_date', None))
        if hire_date and hire_date > timezone.now().date():
            raise serializers.ValidationError('Hire date cannot be in the future')
        return attrs

class AttendanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)

    class Meta:
        model = Attendance
        fields = '__all__'

    def validate(self, attrs):
        check_in = attrs.get('check_in', getattr(self.instance, 'check_in', None))
        check_out = attrs.get('check_out', getattr(self.instance, 'check_out', None))
        if check_in and check_out and check_out < check_in:
            raise serializers.ValidationError('Check-out time must be after check-in time')
        return attrs

class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = '__all__'

class LeaveRequestSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    leave_type_name = serializers.CharField(source='leave_type.name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.full_name', read_only=True)

    class Meta:
        model = LeaveRequest
        fields = '__all__'

    def validate(self, attrs):
        start_date = attrs.get('start_date', getattr(self.instance, 'start_date', None))
        end_date = attrs.get('end_date', getattr(self.instance, 'end_date', None))
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError('End date must be on or after the start date')
        return attrs

class SalaryStructureSerializer(serializers.ModelSerializer):
    gross_salary = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    total_deductions = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    net_salary = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = SalaryStructure
        fields = '__all__'

class EmployeeSalarySerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    salary_structure_name = serializers.CharField(source='salary_structure.name', read_only=True)

    class Meta:
        model = EmployeeSalary
        fields = '__all__'

class PayslipSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    payroll_run_name = serializers.CharField(source='payroll_run.name', read_only=True)

    class Meta:
        model = Payslip
        fields = '__all__'

class PayrollRunSerializer(serializers.ModelSerializer):
    payslip_count = serializers.IntegerField(source='payslips.count', read_only=True)
    payslips = PayslipSerializer(many=True, read_only=True)

    class Meta:
        model = PayrollRun
        fields = '__all__'

    def validate(self, attrs):
        period_start = attrs.get('period_start', getattr(self.instance, 'period_start', None))
        period_end = attrs.get('period_end', getattr(self.instance, 'period_end', None))
        if period_start and period_end and period_end < period_start:
            raise serializers.ValidationError('Period end must be on or after period start')
        return attrs
