from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.core.workflow import run_side_effect, validate_transition

from .models import EmployeeTermination  # noqa: F401
from .models import Department, Employee, LeaveRequest, Payroll, Team

LEAVE_TRANSITIONS = {
    "Pending": {"Approved", "Rejected", "Cancelled"},
    "Approved": {"Cancelled"},
    "Rejected": set(),
    "Cancelled": set(),
}

PAYROLL_TRANSITIONS = {
    "Draft": {"Approved", "Cancelled"},
    "Approved": {"Paid", "Cancelled"},
    "Paid": set(),
    "Cancelled": set(),
}


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = "__all__"


# HR-CTRL-001: roles allowed to see pay data at all.
SALARY_VISIBLE_ROLES = ["HR Manager", "HR", "Finance Manager", "CFO"]


class SalaryVisibilityMixin:
    """HR-CTRL-001: strip pay figures for anyone outside HR and Finance.

    NOTE: the spec also asks for salary data to be *encrypted*. This implements
    the access restriction only. Encryption at rest needs key management that
    doesn't exist in this project yet, and a field that merely looks encrypted
    would be worse than an honest plaintext column — so it is deliberately not
    claimed here.

    An employee may always see their own pay; that isn't a confidentiality
    breach, and hiding it would make the record useless to the person it
    describes.
    """

    SALARY_FIELDS = []

    def _viewer(self):
        request = self.context.get("request")
        return getattr(request, "user", None) if request else None

    def _may_see_salaries(self, instance=None):
        from apps.rbac.models import RoleAssignment

        user = self._viewer()
        if user is None or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        if instance is not None and self._is_own_record(instance, user):
            return True
        return RoleAssignment.objects.filter(
            user=user, role__name__in=SALARY_VISIBLE_ROLES
        ).exists()

    def _is_own_record(self, instance, user):
        return getattr(instance, "user_id", None) == user.pk

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not self._may_see_salaries(instance):
            for field in self.SALARY_FIELDS:
                data.pop(field, None)
        return data


class EmployeeSerializer(SalaryVisibilityMixin, serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True, default="")
    full_name = serializers.SerializerMethodField()

    SALARY_FIELDS = ["salary"]

    def validate(self, data):
        """HR-CTRL-002 is preventive: refuse the activation itself."""
        new_status = data.get("status", getattr(self.instance, "status", None))
        if new_status == "Active":
            probe = self.instance or Employee(**{
                k: v for k, v in data.items() if k != "status"
            })
            for k, v in data.items():
                if k != "status":
                    setattr(probe, k, v)
            try:
                probe.check_hiring_approval()
            except DjangoValidationError as exc:
                raise serializers.ValidationError(exc.messages[0])
        return data

    class Meta:
        model = Employee
        fields = "__all__"

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = "__all__"


class LeaveRequestSerializer(serializers.ModelSerializer):
    duration_days = serializers.ReadOnlyField()
    remaining_balance = serializers.ReadOnlyField()
    employee_name = serializers.SerializerMethodField()

    class Meta:
        model = LeaveRequest
        fields = "__all__"

    def get_employee_name(self, obj):
        return f"{obj.employee.first_name} {obj.employee.last_name}".strip()

    def validate(self, data):
        start = data.get("start_date", getattr(self.instance, "start_date", None))
        end = data.get("end_date", getattr(self.instance, "end_date", None))
        employee = data.get("employee", getattr(self.instance, "employee", None))

        if start and end and end < start:
            raise serializers.ValidationError("End date cannot be before start date.")

        new_status = data.get("status", getattr(self.instance, "status", None))
        if new_status == "Approved":
            # HR-CTRL-003 is preventive: refuse the approval, don't just report
            # a negative balance afterwards.
            probe = self.instance or LeaveRequest(**{
                k: v for k, v in data.items() if k != "status"
            })
            for k, v in data.items():
                if k != "status":
                    setattr(probe, k, v)
            try:
                probe.check_balance()
            except DjangoValidationError as exc:
                raise serializers.ValidationError(exc.messages[0])

        if employee and start and end:
            overlapping = LeaveRequest.objects.filter(
                employee=employee,
                status__in=["Pending", "Approved"],
                start_date__lte=end,
                end_date__gte=start,
            )
            if self.instance:
                overlapping = overlapping.exclude(pk=self.instance.pk)
            if overlapping.exists():
                raise serializers.ValidationError(
                    "This employee already has a pending or approved leave request overlapping these dates."
                )

        new_status = data.get("status")
        if self.instance and new_status and new_status != self.instance.status:
            validate_transition(LEAVE_TRANSITIONS, self.instance.status, new_status)
        return data

    def update(self, instance, validated_data):
        old_status = instance.status
        new_status = validated_data.get("status", old_status)
        instance = super().update(instance, validated_data)
        if old_status != new_status and new_status in ("Approved", "Rejected"):
            from .tasks import send_leave_decision_email

            send_leave_decision_email(instance.id, new_status)
        return instance


class PayrollSerializer(SalaryVisibilityMixin, serializers.ModelSerializer):
    SALARY_FIELDS = [
        "basic_salary", "housing_allowance", "transport_allowance", "food_allowance",
        "other_allowances", "bonuses", "overtime_amount", "gross_salary",
        "total_deductions", "net_salary", "base_hourly_rate", "overtime_rate",
        "social_insurance", "health_insurance", "loan_deductions",
        "advance_payments", "deductions", "tax", "bank_account",
    ]

    def _is_own_record(self, instance, user):
        return getattr(instance.employee, "user_id", None) == user.pk

    overtime_amount = serializers.ReadOnlyField()
    gross_salary = serializers.ReadOnlyField()
    total_deductions = serializers.ReadOnlyField()
    net_salary = serializers.ReadOnlyField()
    employee_name = serializers.SerializerMethodField()

    class Meta:
        model = Payroll
        fields = "__all__"
        read_only_fields = ["posted_to_ledger"]

    def get_employee_name(self, obj):
        return f"{obj.employee.first_name} {obj.employee.last_name}".strip()

    def validate(self, data):
        employee = data.get("employee", getattr(self.instance, "employee", None))
        start = data.get(
            "pay_period_start", getattr(self.instance, "pay_period_start", None)
        )
        end = data.get("pay_period_end", getattr(self.instance, "pay_period_end", None))

        if start and end and end < start:
            raise serializers.ValidationError(
                "Pay period end cannot be before its start."
            )

        if employee and start and end:
            overlapping = Payroll.objects.filter(
                employee=employee,
                pay_period_start__lte=end,
                pay_period_end__gte=start,
            ).exclude(status="Cancelled")
            if self.instance:
                overlapping = overlapping.exclude(pk=self.instance.pk)
            if overlapping.exists():
                raise serializers.ValidationError(
                    "A payroll record already exists for this employee covering an overlapping period."
                )

        new_status = data.get("status")
        if self.instance and new_status and new_status != self.instance.status:
            validate_transition(PAYROLL_TRANSITIONS, self.instance.status, new_status)
        return data

    def update(self, instance, validated_data):
        old_status = instance.status
        new_status = validated_data.get("status", old_status)
        instance = super().update(instance, validated_data)
        if old_status != new_status and new_status == "Paid":
            run_side_effect(instance.post_to_ledger)

            from .tasks import send_payroll_paid_email

            send_payroll_paid_email(instance.id)
        return instance


class EmployeeTerminationSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeTermination
        fields = "__all__"
        read_only_fields = ["status", "created_at"]

    def get_employee_name(self, obj):
        return f"{obj.employee.first_name} {obj.employee.last_name}".strip()
