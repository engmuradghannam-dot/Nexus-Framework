from rest_framework import serializers

from apps.core.workflow import validate_transition

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


class EmployeeSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True, default="")
    full_name = serializers.SerializerMethodField()

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


class PayrollSerializer(serializers.ModelSerializer):
    overtime_amount = serializers.ReadOnlyField()
    gross_salary = serializers.ReadOnlyField()
    total_deductions = serializers.ReadOnlyField()
    net_salary = serializers.ReadOnlyField()
    employee_name = serializers.SerializerMethodField()

    class Meta:
        model = Payroll
        fields = "__all__"

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
            from .tasks import send_payroll_paid_email

            send_payroll_paid_email(instance.id)
        return instance
