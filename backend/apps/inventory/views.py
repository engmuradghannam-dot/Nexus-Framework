from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from .models import Item, ItemGroup, StockEntry
from .serializers import ItemSerializer, ItemGroupSerializer, StockEntrySerializer

class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['item_code', 'item_name', 'description']
    filterset_fields = ['item_group', 'is_stock_item', 'company']

class ItemGroupViewSet(viewsets.ModelViewSet):
    queryset = ItemGroup.objects.all()
    serializer_class = ItemGroupSerializer
    filter_backends = [SearchFilter]
    search_fields = ['name']

class StockEntryViewSet(viewsets.ModelViewSet):
    queryset = StockEntry.objects.all()
    serializer_class = StockEntrySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['warehouse', 'item', 'entry_type']
