from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.tenants.mixins import TenantScopedMixin

from .models import (Appraisal, EmployeeLoan, ExpenseClaim, JobApplicant,
                     JobOpening, end_of_service)
from .serializers import (AppraisalSerializer, EmployeeLoanSerializer,
                          ExpenseClaimSerializer, JobApplicantSerializer,
                          JobOpeningSerializer)


class ExpenseClaimViewSet(TenantScopedMixin, viewsets.ModelViewSet):
    queryset = ExpenseClaim.objects.all()
    serializer_class = ExpenseClaimSerializer

    @action(detail=True, methods=["post"])
    def set_status(self, request, pk=None):
        claim = self.get_object()
        st = request.data.get("status")
        if st in dict(ExpenseClaim.STATUS):
            claim.status = st; claim.save(update_fields=["status"])
        return Response(self.get_serializer(claim).data)


class EmployeeLoanViewSet(TenantScopedMixin, viewsets.ModelViewSet):
    queryset = EmployeeLoan.objects.all()
    serializer_class = EmployeeLoanSerializer

    @action(detail=True, methods=["post"])
    def pay_installment(self, request, pk=None):
        loan = self.get_object()
        if loan.paid_installments < loan.installments:
            loan.paid_installments += 1
            if loan.paid_installments >= loan.installments:
                loan.status = "settled"
            loan.save()
        return Response(self.get_serializer(loan).data)


class JobOpeningViewSet(TenantScopedMixin, viewsets.ModelViewSet):
    queryset = JobOpening.objects.all()
    serializer_class = JobOpeningSerializer


class JobApplicantViewSet(TenantScopedMixin, viewsets.ModelViewSet):
    queryset = JobApplicant.objects.all()
    serializer_class = JobApplicantSerializer
    filterset_fields = ["opening", "stage"]

    def get_queryset(self):
        qs = super().get_queryset()
        opening = self.request.query_params.get("opening")
        return qs.filter(opening=opening) if opening else qs


class AppraisalViewSet(TenantScopedMixin, viewsets.ModelViewSet):
    queryset = Appraisal.objects.all()
    serializer_class = AppraisalSerializer


class EndOfServiceView(APIView):
    """Compute Saudi end-of-service gratuity."""
    def get(self, request):
        try:
            wage = float(request.query_params.get("last_wage", 0))
            years = float(request.query_params.get("years", 0))
        except ValueError:
            return Response({"error": "قيم غير صالحة"}, status=400)
        reason = request.query_params.get("reason", "termination")
        amount = end_of_service(wage, years, reason)
        return Response({"last_wage": wage, "years": years, "reason": reason, "gratuity": float(amount)})
