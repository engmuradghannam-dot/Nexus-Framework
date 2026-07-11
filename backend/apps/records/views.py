from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets

from .models import ModuleRecord
from .serializers import ModuleRecordSerializer


class ModuleRecordViewSet(viewsets.ModelViewSet):
    queryset = ModuleRecord.objects.all()
    serializer_class = ModuleRecordSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["module"]

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(created_by=user)
