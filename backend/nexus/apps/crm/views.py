from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Contact, Customer, CustomerInteraction, Opportunity
from .serializers import ContactSerializer, CustomerInteractionSerializer, CustomerSerializer, OpportunitySerializer


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.select_related('branch', 'assigned_sales_rep').all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['get'])
    def duplicates(self, request, pk=None):
        # CRM-CTRL-002 Duplicate Prevention
        customer = self.get_object()
        duplicates = Customer.find_duplicates(email=customer.email, phone=customer.phone, exclude_pk=customer.pk)
        serializer = self.get_serializer(duplicates, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def check_credit(self, request, pk=None):
        # CRM-CTRL-001 / SAL-CTRL-001 Credit Limit Check
        customer = self.get_object()
        amount = request.data.get('order_amount', 0)
        try:
            amount = float(amount)
        except (TypeError, ValueError):
            return Response({"error": "invalid order_amount"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            'blocked': customer.exceeds_credit_limit(amount),
            'credit_available': str(customer.credit_available()),
        })

    @action(detail=True, methods=['post'])
    def recalculate_score(self, request, pk=None):
        # CRM-RULE-001 Lead Scoring
        customer = self.get_object()
        return Response({'lead_score': customer.calculate_score()})


class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.select_related('customer').all()
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated]


class CustomerInteractionViewSet(viewsets.ModelViewSet):
    queryset = CustomerInteraction.objects.select_related('customer').all()
    serializer_class = CustomerInteractionSerializer
    permission_classes = [IsAuthenticated]


class OpportunityViewSet(viewsets.ModelViewSet):
    queryset = Opportunity.objects.select_related('customer', 'assigned_to').all()
    serializer_class = OpportunitySerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def needs_follow_up(self, request):
        # CRM-RULE-003 Auto-Follow-up
        opportunities = [o for o in self.get_queryset() if o.needs_follow_up()]
        serializer = self.get_serializer(opportunities, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def pipeline_summary(self, request):
        # CRM-CTRL-003 Sales Pipeline Audit
        summary = {}
        for stage, label in Opportunity.STAGE_CHOICES:
            qs = self.get_queryset().filter(stage=stage)
            summary[stage] = {'count': qs.count(), 'value': str(sum((o.value for o in qs), 0))}
        return Response(summary)
