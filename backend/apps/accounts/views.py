from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from .models import Account, JournalEntry
from .serializers import AccountSerializer, JournalEntrySerializer

class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['account_name', 'account_number']
    filterset_fields = ['account_type', 'company']

class JournalEntryViewSet(viewsets.ModelViewSet):
    queryset = JournalEntry.objects.all()
    serializer_class = JournalEntrySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['entry_number', 'reference']
    filterset_fields = ['status', 'company']
