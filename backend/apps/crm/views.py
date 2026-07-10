from rest_framework import viewsets

from apps.core.mixins import CompanyScopedMixin

from .models import Lead, Opportunity
from .serializers import LeadSerializer, OpportunitySerializer


class LeadViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    company_field = "company"


class OpportunityViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = Opportunity.objects.all()
    serializer_class = OpportunitySerializer
    company_field = "company"
