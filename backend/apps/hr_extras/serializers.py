from rest_framework import serializers

from .models import Appraisal, EmployeeLoan, ExpenseClaim, JobApplicant, JobOpening


class ExpenseClaimSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseClaim
        fields = "__all__"
        read_only_fields = ["tenant"]


class EmployeeLoanSerializer(serializers.ModelSerializer):
    monthly = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    remaining = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = EmployeeLoan
        fields = "__all__"
        read_only_fields = ["tenant"]


class JobOpeningSerializer(serializers.ModelSerializer):
    applicant_count = serializers.SerializerMethodField()

    class Meta:
        model = JobOpening
        fields = "__all__"
        read_only_fields = ["tenant"]

    def get_applicant_count(self, obj):
        return obj.applicants.count()


class JobApplicantSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobApplicant
        fields = "__all__"
        read_only_fields = ["tenant"]


class AppraisalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appraisal
        fields = "__all__"
        read_only_fields = ["tenant"]
