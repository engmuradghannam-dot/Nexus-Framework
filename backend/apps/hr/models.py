from decimal import Decimal

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
        ("Pending Approval", "Pending Approval"),
        ("Active", "Active"),
        ("Inactive", "Inactive"),
        ("On Leave", "On Leave"),
        ("Terminated", "Terminated"),
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
    approved_by_dept_head = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="hires_approved_as_dept_head",
        help_text="HR-CTRL-002: department head sign-off on this hire.",
    )
    approved_by_hr = models.ForeignKey(
        "core.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="hires_approved_as_hr",
        help_text="HR-CTRL-002: HR sign-off. Both are required before the "
        "employee can be made Active.",
    )
    probation_reviewed_at = models.DateField(
        null=True, blank=True,
        help_text="HR-RULE-002: set when the probation review is completed. "
        "While null and the 90-day window has passed, the employee is flagged.",
    )
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

    @property
    def policy(self):
        return HRPolicy.for_company(self.company)

    def tenure_years(self, as_of=None):
        """Years of service as a decimal. 365.25 absorbs leap years."""
        from datetime import date

        if not self.date_of_joining:
            return Decimal(0)
        as_of = as_of or date.today()
        days = (as_of - self.date_of_joining).days
        if days <= 0:
            return Decimal(0)
        return (Decimal(days) / Decimal("365.25")).quantize(Decimal("0.01"))

    def leave_entitlement_days(self, as_of=None):
        """HR-RULE-001: annual leave this employee is entitled to.

        Resolves the LeaveEntitlement rule HR configured for this employment
        type and tenure, preferring a type-specific rule over a catch-all and
        the highest tenure band the employee has actually reached. Falls back to
        the company default only when nothing matches, so an unconfigured
        company keeps its previous behaviour instead of silently dropping
        everyone to zero days.
        """
        tenure = self.tenure_years(as_of)
        rules = LeaveEntitlement.objects.filter(
            company=self.company, is_active=True, min_tenure_years__lte=tenure,
        )
        specific = rules.filter(employment_type=self.employment_type).first()
        if specific:
            return Decimal(specific.days_per_year)
        catch_all = rules.filter(employment_type="").first()
        if catch_all:
            return Decimal(catch_all.days_per_year)
        return Decimal(self.policy.default_annual_leave_days)

    def monthly_leave_accrual(self, as_of=None):
        """HR-RULE-001: days earned per month at the current entitlement."""
        return (self.leave_entitlement_days(as_of) / Decimal(12)).quantize(Decimal("0.01"))

    def end_of_service_benefit(self, as_of=None, resigned=False):
        """HR-RULE-003: end-of-service benefit, from HR's own bands.

        This function contains no statutory numbers. It applies whatever bands
        HR configured, in order, against the employee's tenure. With no policy
        configured it raises rather than returning zero — this figure lands in
        somebody's final pay, and a silent zero is the most dangerous wrong
        number there is.
        """
        from django.core.exceptions import ValidationError as DjangoValidationError

        policy = EndOfServicePolicy.objects.filter(company=self.company).first()
        if policy is None or not policy.bands.exists():
            raise DjangoValidationError(
                "No end-of-service policy is configured for this company. HR must "
                "define the tenure bands before a benefit can be calculated."
            )
        wage = Decimal(self.salary or 0)
        if policy.wage_basis == "gross":
            latest = self.payrolls.order_by("-pay_period_end").first()
            if latest:
                wage = Decimal(latest.gross_salary)
        tenure = self.tenure_years(as_of)
        total_months = Decimal(0)
        breakdown = []
        for band in policy.bands.order_by("from_years"):
            lower = Decimal(band.from_years)
            upper = Decimal(band.to_years) if band.to_years is not None else tenure
            years_in_band = min(tenure, upper) - lower
            if years_in_band <= 0:
                continue
            months = years_in_band * Decimal(band.months_per_year)
            if resigned:
                months *= Decimal(band.resignation_fraction)
            total_months += months
            breakdown.append({
                "band": str(band),
                "years_counted": years_in_band.quantize(Decimal("0.01")),
                "months_accrued": months.quantize(Decimal("0.01")),
            })
        return {
            "tenure_years": tenure,
            "wage_basis": policy.wage_basis,
            "monthly_wage": wage,
            "months_accrued": total_months.quantize(Decimal("0.01")),
            "amount": (wage * total_months).quantize(Decimal("0.01")),
            "resigned": resigned,
            "breakdown": breakdown,
        }

    def check_hiring_approval(self):
        """HR-CTRL-002: a new hire needs both the department head and HR before
        they become Active. Existing employees are grandfathered — they predate
        this control and were never routed through it."""
        from django.core.exceptions import ValidationError as DjangoValidationError

        if self.pk:
            previous = Employee.objects.filter(pk=self.pk).values_list(
                "status", flat=True
            ).first()
            if previous not in (None, "Pending Approval"):
                return
        missing = []
        if self.approved_by_dept_head_id is None:
            missing.append("department head")
        if self.approved_by_hr_id is None:
            missing.append("HR")
        if missing:
            raise DjangoValidationError(
                f"New hire requires approval from {' and '.join(missing)} before "
                f"activation."
            )

    @property
    def probation_end_date(self):
        """HR-RULE-002: hire date + the probation length HR configured."""
        from datetime import timedelta

        if not self.date_of_joining:
            return None
        return self.date_of_joining + timedelta(days=self.policy.probation_days)

    @property
    def probation_review_due(self):
        """HR-RULE-002: the probation window has closed and no review is on
        record yet.

        Probation is tracked by its own review date rather than by
        employment_type — the type choices are Full-time/Part-time/Contract/
        Intern, none of which say anything about probation, so keying off them
        would have made this permanently False.
        """
        from datetime import date

        if self.probation_reviewed_at is not None:
            return False
        if self.status and self.status != "Active":
            return False
        end = self.probation_end_date
        return end is not None and date.today() >= end

    @property
    def days_to_probation_end(self):
        from datetime import date

        end = self.probation_end_date
        return None if end is None else (end - date.today()).days

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
        ANNUAL_ALLOWANCE = self.employee.leave_entitlement_days()
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
        ANNUAL_ALLOWANCE = self.employee.leave_entitlement_days()
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


# HR-RULE-004: the 1.5x/2x multipliers from ERP_Complete_System.xlsx now live on
# HRPolicy as defaults rather than as constants here — they are HR's to set, and
# a company needing different ones shouldn't need a redeploy to get them.


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
    overtime_hours = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text="Legacy flat-rate overtime hours, paid at overtime_rate with no "
        "multiplier. Superseded by the weekday/holiday split below.",
    )
    overtime_rate = models.DecimalField(
        max_digits=18, decimal_places=2, default=0,
        help_text="Legacy flat overtime rate per hour.",
    )
    base_hourly_rate = models.DecimalField(
        max_digits=18, decimal_places=2, default=0,
        help_text="HR-RULE-004: ordinary hourly wage. Overtime multipliers apply "
        "on top of this, so it must be the plain rate, not a pre-multiplied one.",
    )
    overtime_weekday_hours = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text="HR-RULE-004: paid at 1.5x base_hourly_rate.",
    )
    overtime_holiday_hours = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text="HR-RULE-004: weekend/holiday overtime, paid at 2x base_hourly_rate.",
    )
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
        """HR-RULE-004: 1.5x on weekdays, 2x on weekends/holidays.

        The legacy fields (overtime_hours x overtime_rate, flat, no multiplier)
        are kept and still honoured, because it was never defined whether
        overtime_rate held the ordinary hourly wage or an already-multiplied
        one. Silently applying 1.5x to existing rows could have doubled real
        salaries, so the multiplier only applies to the new, explicitly-named
        fields; the legacy path is untouched. Both are summed, so a payroll can
        migrate one period at a time.
        """
        legacy = (self.overtime_hours or Decimal(0)) * (self.overtime_rate or Decimal(0))
        base = self.base_hourly_rate or Decimal(0)
        policy = self.employee.policy
        weekday = (
            (self.overtime_weekday_hours or Decimal(0))
            * base * Decimal(policy.overtime_weekday_multiplier)
        )
        holiday = (
            (self.overtime_holiday_hours or Decimal(0))
            * base * Decimal(policy.overtime_holiday_multiplier)
        )
        return (legacy + weekday + holiday).quantize(Decimal("0.01"))

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
                    branch=self.employee.branch,
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


class EmployeeTermination(models.Model):
    """HR-CTRL-004: every termination logged with its reason and approval chain.

    Employee.status could be flipped straight to Inactive by anyone, leaving no
    record of why, who asked, or who agreed. This is the audit trail that
    control requires.
    """

    REASON_CHOICES = [
        ("Resignation", "Resignation"),
        ("End of Contract", "End of Contract"),
        ("Redundancy", "Redundancy"),
        ("Dismissal", "Dismissal"),
        ("Retirement", "Retirement"),
        ("Other", "Other"),
    ]
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
    ]
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="terminations"
    )
    termination_date = models.DateField()
    reason = models.CharField(max_length=50, choices=REASON_CHOICES)
    reason_detail = models.TextField(
        blank=True, help_text="Free-text narrative behind the reason code."
    )
    requested_by = models.ForeignKey(
        "core.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="terminations_requested",
    )
    approved_by_manager = models.ForeignKey(
        Employee, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="terminations_approved_as_manager",
    )
    approved_by_hr = models.ForeignKey(
        "core.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="terminations_approved_as_hr",
    )
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="Pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-termination_date", "-id"]

    def __str__(self):
        return f"{self.employee} — {self.reason} ({self.termination_date})"

    def approve(self):
        """Complete the chain and take the employee off the roll.

        Both a manager and HR must have signed, and they must not be the same
        person acting twice — a one-signature termination is not an approval
        chain.
        """
        from django.core.exceptions import ValidationError as DjangoValidationError
        from django.db import transaction as db_transaction

        if self.status != "Pending":
            raise DjangoValidationError(
                f"Only a pending termination can be approved (this one is "
                f"'{self.status}')."
            )
        missing = []
        if self.approved_by_manager_id is None:
            missing.append("manager")
        if self.approved_by_hr_id is None:
            missing.append("HR")
        if missing:
            raise DjangoValidationError(
                f"Termination requires approval from {' and '.join(missing)}."
            )
        manager_user = self.approved_by_manager.user
        if manager_user and manager_user.pk == self.approved_by_hr_id:
            raise DjangoValidationError(
                "The approval chain needs two different people; one user cannot "
                "sign as both manager and HR."
            )
        with db_transaction.atomic():
            self.status = "Approved"
            self.save(update_fields=["status"])
            Employee.objects.filter(pk=self.employee_id).update(status="Terminated")
        return True, "تم إنهاء الخدمة / Termination approved"


class HRPolicy(models.Model):
    """Company-level HR parameters that HR maintains, not the code.

    Probation length, overtime multipliers and leave allowance were hardcoded
    constants (90 days, 1.5x, 2x, 21 days). They are policy, not physics: they
    differ by company and change over time, and a company that needed different
    numbers had to be redeployed to get them.

    Every field has the previously-hardcoded value as its default, so a company
    with no policy row behaves exactly as before.
    """

    company = models.OneToOneField(
        Company, on_delete=models.CASCADE, related_name="hr_policy"
    )
    probation_days = models.PositiveIntegerField(default=90)
    overtime_weekday_multiplier = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("1.5")
    )
    overtime_holiday_multiplier = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("2")
    )
    default_annual_leave_days = models.PositiveIntegerField(
        default=21,
        help_text="Used when no LeaveEntitlement rule matches the employee.",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "HR policies"

    def __str__(self):
        return f"HR policy — {self.company}"

    @classmethod
    def for_company(cls, company):
        """Never creates a row: reading a policy shouldn't write to the database.
        Returns an unsaved instance carrying the defaults when none exists."""
        if company is None:
            return cls()
        return cls.objects.filter(company=company).first() or cls(company=company)


class LeaveEntitlement(models.Model):
    """HR-RULE-001: how much annual leave accrues, per employment type and tenure.

    The spec says leave accrues 'based on employment type and tenure' and gives
    no rates — because they're HR's to set. This is where HR sets them.

    Resolution picks the most specific match: the rule with the highest
    min_tenure_years the employee has actually reached, for their employment
    type, preferring a type-specific rule over a catch-all.
    """

    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="leave_entitlements"
    )
    employment_type = models.CharField(
        max_length=50, blank=True,
        help_text="Blank means it applies to every employment type.",
    )
    min_tenure_years = models.PositiveIntegerField(
        default=0, help_text="Applies once the employee has served this many years."
    )
    days_per_year = models.DecimalField(max_digits=6, decimal_places=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-min_tenure_years", "employment_type"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "employment_type", "min_tenure_years"],
                name="unique_leave_entitlement_rule",
            )
        ]

    def __str__(self):
        scope = self.employment_type or "all types"
        return f"{scope}, {self.min_tenure_years}+ yrs → {self.days_per_year} days"

    @property
    def days_per_month(self):
        """HR-RULE-001: the monthly accrual this entitlement implies."""
        return (Decimal(self.days_per_year) / Decimal(12)).quantize(Decimal("0.01"))


class EndOfServicePolicy(models.Model):
    """HR-RULE-003: the end-of-service benefit rules, as HR defines them.

    Deliberately holds no numbers of its own. Saudi Labor Law states the shape
    (a fraction of wage per year of service, banded by tenure, reduced on
    resignation) but the exact fractions and bands are a legal reading that HR
    and legal own — not something to hardcode from memory into a calculation
    that lands in someone's final pay.

    A company with no bands configured gets no calculation and an explicit
    error, never a silent zero or an invented figure.
    """

    company = models.OneToOneField(
        Company, on_delete=models.CASCADE, related_name="eosb_policy"
    )
    wage_basis = models.CharField(
        max_length=20,
        choices=[("basic", "Basic salary"), ("gross", "Gross salary")],
        default="basic",
        help_text="Which wage the per-year fraction applies to.",
    )
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "End of service policies"

    def __str__(self):
        return f"EOSB policy — {self.company}"


class EndOfServiceBand(models.Model):
    """One tenure band of an EndOfServicePolicy.

    Example a company might enter: 0–5 years at 0.5 months of wage per year,
    5+ years at 1.0. The resignation_fraction then scales the entitlement when
    the employee resigns rather than being let go.
    """

    policy = models.ForeignKey(
        EndOfServicePolicy, on_delete=models.CASCADE, related_name="bands"
    )
    from_years = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    to_years = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="Leave blank for 'and above'.",
    )
    months_per_year = models.DecimalField(
        max_digits=5, decimal_places=3,
        help_text="Months of wage accrued per year of service inside this band.",
    )
    resignation_fraction = models.DecimalField(
        max_digits=5, decimal_places=3, default=Decimal("1"),
        help_text="Multiplier applied to this band's entitlement when the "
        "employee resigns. 1 means resignation is treated the same as "
        "termination.",
    )

    class Meta:
        ordering = ["from_years"]

    def __str__(self):
        upper = self.to_years if self.to_years is not None else "∞"
        return f"{self.from_years}–{upper} yrs: {self.months_per_year} mo/yr"
