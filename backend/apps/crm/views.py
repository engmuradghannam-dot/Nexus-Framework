from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from .models import Lead, Opportunity
from .serializers import LeadSerializer, OpportunitySerializer

class LeadViewSet(viewsets.ModelViewSet):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['lead_name', 'organization', 'email']
    filterset_fields = ['status', 'company']

class OpportunityViewSet(viewsets.ModelViewSet):
    queryset = Opportunity.objects.all()
    serializer_class = OpportunitySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['opportunity_name', 'customer_name']
    filterset_fields = ['status', 'company']
