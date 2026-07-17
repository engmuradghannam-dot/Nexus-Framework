from django.core.validators import FileExtensionValidator
from django.db import models

from apps.core.models import Branch, Company, User
from apps.core.validators import ALLOWED_IMAGE_EXTENSIONS, validate_image_size


class Department(models.Model):
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="departments"
    )
    name = models.CharField(max_length=255)
    parent_department = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True
    )

    def __str__(self):
        return self.name


class Employee(models.Model):
    GENDER_CHOICES = [("Male", "Male"), ("Female", "Female"), ("Other", "Other")]
    STATUS_CHOICES = [
        ("Active", "Active"),
        ("Inactive", "Inactive"),
        ("On Leave", "On Leave"),
    ]
    MARITAL_STATUS_CHOICES = [
        ("Single", "Single"),
        ("Married", "Married"),
        ("Divorced", "Divorced"),
        ("Widowed", "Widowed"),
    ]
    EMPLOYMENT_TYPE_CHOICES = [
        ("Full-time", "Full-time"),
        ("Part-time", "Part-time"),
        ("Contract", "Contract"),
        ("Intern", "Intern"),
    ]
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="employees"
    )
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True
    )
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employee_profile",
        help_text='Login account for this employee, used to scope "my tasks".',
    )
    employee_id = models.CharField(max_length=100, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    mobile = models.CharField(max_length=50, blank=True)
    national_id = models.CharField(max_length=100, blank=True)
    passport = models.CharField(max_length=100, blank=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True)
    marital_status = models.CharField(
        max_length=20, choices=MARITAL_STATUS_CHOICES, blank=True
    )
    nationality = models.CharField(max_length=100, blank=True)
    employment_type = models.CharField(
        max_length=50, choices=EMPLOYMENT_TYPE_CHOICES, default="Full-time"
    )
    date_of_birth = models.DateField(null=True, blank=True)
    date_of_joining = models.DateField(null=True, blank=True)
    designation = models.CharField(max_length=255, blank=True)
    job_title = models.CharField(max_length=255, blank=True)
    salary = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default="SAR")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="Active")
    bank_account = models.CharField(max_length=100, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    iban = models.CharField(max_length=50, blank=True)
    emergency_contact_name = models.CharField(max_length=255, blank=True)
    emergency_contact_phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default="Saudi Arabia")
    supervisor = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subordinates",
    )
    photo = models.ImageField(
        upload_to="employee_photos/",
        blank=True,
        null=True,
        validators=[
            validate_image_size,
            FileExtensionValidator(ALLOWED_IMAGE_EXTENSIONS),
        ],
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee_id} - {self.first_name} {self.last_name}"


class Team(models.Model):
    """A working team within a company. Tasks assigned to a team are
    visible to every member of that team."""

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="teams")
    name = models.CharField(max_length=255)
    lead = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="led_teams",
    )
    members = models.ManyToManyField(Employee, related_name="teams", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class LeaveRequest(models.Model):
    LEAVE_TYPES = [
        ("Annual", "Annual"),
        ("Sick", "Sick"),
        ("Unpaid", "Unpaid"),
        ("Maternity", "Maternity"),
        ("Paternity", "Paternity"),
        ("Emergency", "Emergency"),
    ]
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
        ("Cancelled", "Cancelled"),
    ]

    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="leave_requests"
    )
    leave_type = models.CharField(max_length=50, choices=LEAVE_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="Pending")
    approved_by = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_leaves",
    )
    approval_date = models.DateField(null=True, blank=True)
    year = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def duration_days(self):
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0

    def check_balance(self):
        """HR-CTRL-003: an employee cannot take annual leave they haven't got.

        remaining_balance() already computed the figure; nothing ever refused a
        request that blew through it. Only Annual leave carries a balance —
        Sick/Unpaid/Maternity are governed separately and are not capped here.
        """
        from django.core.exceptions import ValidationError as DjangoValidationError

        if self.leave_type != "Annual" or not self.year:
            return
        ANNUAL_ALLOWANCE = 21
        taken = sum(
            (lr.duration_days for lr in LeaveRequest.objects.filter(
                employee=self.employee, leave_type="Annual",
                year=self.year, status="Approved",
            ).exclude(id=self.id)),
            0,
        )
        if taken + self.duration_days > ANNUAL_ALLOWANCE:
            raise DjangoValidationError(
                f"رصيد الإجازات غير كافٍ / Insufficient leave balance: "
                f"{ANNUAL_ALLOWANCE - taken} day(s) remaining, "
                f"{self.duration_days} requested."
            )

    @property
    def remaining_balance(self):
        """Simple annual-leave balance tracker: assumes a 21-day standard
        annual allowance minus approved Annual leave days taken this year."""
        if self.leave_type != "Annual" or not self.year:
            return None
        ANNUAL_ALLOWANCE = 21
        taken = LeaveRequest.objects.filter(
            employee=self.employee,
            leave_type="Annual",
            year=self.year,
            status="Approved",
        ).exclude(id=self.id)
        days_taken = sum((lr.duration_days for lr in taken), 0)
        if self.status == "Approved":
            days_taken += self.duration_days
        return ANNUAL_ALLOWANCE - days_taken

    def save(self, *args, **kwargs):
        if not self.year and self.start_date:
            self.year = self.start_date.year
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee} - {self.leave_type} ({self.start_date} to {self.end_date})"


class Payroll(models.Model):
    PAYMENT_METHODS = [
        ("Bank Transfer", "Bank Transfer"),
        ("Cash", "Cash"),
        ("Cheque", "Cheque"),
    ]
    STATUS_CHOICES = [
        ("Draft", "Draft"),
        ("Approved", "Approved"),
        ("Paid", "Paid"),
        ("Cancelled", "Cancelled"),
    ]

    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="payrolls"
    )
    pay_period_start = models.DateField()
    pay_period_end = models.DateField()
    basic_salary = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    housing_allowance = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    transport_allowance = models.DecimalField(
        max_digits=18, decimal_places=2, default=0
    )
    food_allowance = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    other_allowances = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    overtime_hours = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    overtime_rate = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    bonuses = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    social_insurance = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0,
        help_text="Employee GOSI contribution",
    )
    health_insurance = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    loan_deductions = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    advance_payments = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    deductions = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0,
        help_text="Other/miscellaneous deductions",
    )
    tax = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    payment_method = models.CharField(
        max_length=50, choices=PAYMENT_METHODS, default="Bank Transfer"
    )
    bank_account = models.CharField(max_length=100, blank=True)
    payment_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="Draft")
    currency = models.CharField(max_length=10, default="SAR")
    posted_to_ledger = models.BooleanField(
        default=False, help_text="Whether this payroll's salary expense has been posted to the GL."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def overtime_amount(self):
        return (self.overtime_hours or 0) * (self.overtime_rate or 0)

    @property
    def gross_salary(self):
        return (
            self.basic_salary
            + self.housing_allowance
            + self.transport_allowance
            + self.food_allowance
            + self.other_allowances
            + self.overtime_amount
            + self.bonuses
        )

    @property
    def total_deductions(self):
        return (
            self.deductions
            + self.social_insurance
            + self.health_insurance
            + self.loan_deductions
            + self.advance_payments
            + self.tax
        )

    @property
    def net_salary(self):
        return self.gross_salary - self.total_deductions

    def post_to_ledger(self):
        """Post this payroll's salary expense to the GL, mirroring
        Invoice.post_to_ledger(): Dr Salaries Expense (5200) for the full
        gross salary, split across Cr Bank (1200, the net cash paid out)
        and Cr Accounts Payable (2100, standing in for GOSI/tax/loan
        liabilities withheld) so the entry balances by construction
        (gross_salary == net_salary + total_deductions).
        """
        from django.db import transaction

        from apps.accounts.models import Account, AccountingPeriod, JournalEntry

        if self.posted_to_ledger:
            return False, "تم ترحيل هذا الراتب مسبقاً"
        if self.status != "Paid":
            return False, "لا يمكن الترحيل إلا لراتب مدفوع"

        company = self.employee.company
        if company is None:
            return False, "لا توجد شركة"

        post_date = self.payment_date or self.pay_period_end
        if AccountingPeriod.is_locked(company, post_date):
            return False, "الفترة المحاسبية مقفلة لهذا التاريخ"

        def acc(number):
            return Account.objects.filter(company=company, account_number=number).first()

        expense, bank, payable = acc("5200"), acc("1200"), acc("2100")
        if not all([expense, bank]):
            return False, "حسابات الرواتب غير مهيأة — شغّل seed_accounting"

        legs = [(expense, bank, self.net_salary)]
        if self.total_deductions > 0:
            if not payable:
                return False, "حساب الالتزامات غير مهيأ — شغّل seed_accounting"
            legs.append((expense, payable, self.total_deductions))

        # Both legs and the posted flag move together: if the deductions leg
        # fails after the net-pay leg is already written, the GL would be left
        # permanently unbalanced with no way to retry (posted_to_ledger unset,
        # but half the entries already there).
        with transaction.atomic():
            for i, (dr, cr, amt) in enumerate(legs):
                if amt <= 0:
                    continue
                JournalEntry.objects.create(
                    company=company,
                    entry_number=f"PAYROLL-{self.pk}-{i+1}",
                    posting_date=post_date,
                    reference=f"Payroll {self.employee} ({self.pay_period_start} to {self.pay_period_end})",
                    debit_account=dr, credit_account=cr, amount=amt,
                    total_debit=amt, total_credit=amt, status="Submitted",
                )
                dr.post(debit_amount=amt)
                cr.post(credit_amount=amt)

            self.posted_to_ledger = True
            self.save(update_fields=["posted_to_ledger"])
        return True, "تم ترحيل الراتب إلى دفتر الأستاذ"

    def __str__(self):
        return f"{self.employee} - {self.pay_period_start} to {self.pay_period_end}"
