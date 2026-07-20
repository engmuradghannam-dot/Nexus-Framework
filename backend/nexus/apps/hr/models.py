from django.core.validators import MinLengthValidator, MinValueValidator
from django.db import models
from django.contrib.auth.models import User

from nexus.apps.core.models import Company, Branch, Department
from nexus.apps.core.utils import generate_code
from nexus.apps.core.validators import alphanumeric_validator, letters_only_validator, phone_validator

class Employee(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('on_leave', 'On Leave'),
        ('terminated', 'Terminated'),
        ('suspended', 'Suspended'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee', null=True, blank=True, db_constraint=False)
    employee_id = models.CharField(max_length=50, unique=True, blank=True)  # EMP-YYYY-#####
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='employees')
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')
    first_name = models.CharField(max_length=100, validators=[letters_only_validator, MinLengthValidator(2)])
    last_name = models.CharField(max_length=100, validators=[letters_only_validator, MinLengthValidator(2)])
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True, validators=[phone_validator])
    hire_date = models.DateField()
    job_title = models.CharField(max_length=255)
    salary = models.DecimalField(max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subordinates')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.employee_id:
            self.employee_id = generate_code(Employee, 'employee_id', 'EMP')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee_id} - {self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def clean(self):
        from django.core.exceptions import ValidationError
        from django.utils import timezone
        if self.manager_id and self.manager_id == self.pk:
            raise ValidationError('Employee cannot be their own manager')
        if self.hire_date and self.hire_date > timezone.now().date():
            raise ValidationError('Hire date cannot be in the future')

class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('half_day', 'Half Day'),
        ('on_leave', 'On Leave'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='present')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['employee', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.employee.full_name} - {self.date}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.check_in and self.check_out and self.check_out < self.check_in:
            raise ValidationError('Check-out time must be after check-in time')

class LeaveType(models.Model):
    name = models.CharField(max_length=100, validators=[MinLengthValidator(2)])
    code = models.CharField(max_length=50, unique=True, validators=[alphanumeric_validator])
    days_per_year = models.PositiveIntegerField(default=0)
    is_paid = models.BooleanField(default=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE, related_name='requests')
    start_date = models.DateField()
    end_date = models.DateField()
    days = models.PositiveIntegerField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves')
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee.full_name} - {self.leave_type.name}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError('End date must be on or after the start date')

class SalaryStructure(models.Model):
    name = models.CharField(max_length=255, validators=[MinLengthValidator(2)])
    code = models.CharField(max_length=50, unique=True, validators=[alphanumeric_validator])
    basic_salary = models.DecimalField(max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    housing_allowance = models.DecimalField(max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    transport_allowance = models.DecimalField(max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    other_allowances = models.DecimalField(max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    tax_deduction = models.DecimalField(max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    insurance_deduction = models.DecimalField(max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    other_deductions = models.DecimalField(max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def gross_salary(self):
        return self.basic_salary + self.housing_allowance + self.transport_allowance + self.other_allowances

    @property
    def total_deductions(self):
        return self.tax_deduction + self.insurance_deduction + self.other_deductions

    @property
    def net_salary(self):
        return self.gross_salary - self.total_deductions

    def __str__(self):
        return self.name

class EmployeeSalary(models.Model):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='salary_structure')
    salary_structure = models.ForeignKey(SalaryStructure, on_delete=models.CASCADE, related_name='employees')
    effective_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee.full_name} - {self.salary_structure.name}"

class PayrollRun(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('paid', 'Paid'),
    ]

    name = models.CharField(max_length=255, validators=[MinLengthValidator(2)])
    period_start = models.DateField()
    period_end = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    total_gross = models.DecimalField(max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    total_deductions = models.DecimalField(max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    total_net = models.DecimalField(max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.period_start} - {self.period_end})"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.period_start and self.period_end and self.period_end < self.period_start:
            raise ValidationError('Period end must be on or after period start')

class Payslip(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
    ]

    payroll_run = models.ForeignKey(PayrollRun, on_delete=models.CASCADE, related_name='payslips')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payslips')
    basic_salary = models.DecimalField(max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    allowances = models.DecimalField(max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    deductions = models.DecimalField(max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    net_salary = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee.full_name} - {self.payroll_run.name}"
