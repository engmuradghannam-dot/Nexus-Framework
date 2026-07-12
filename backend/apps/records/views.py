from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets

from apps.audit.models import record_audit

from .models import ModuleRecord
from .serializers import ModuleRecordSerializer


class ModuleRecordViewSet(viewsets.ModelViewSet):
    queryset = ModuleRecord.objects.all()
    serializer_class = ModuleRecordSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["module"]

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        obj = serializer.save(created_by=user)
        record_audit(self.request, "create", obj.module, obj.pk, obj.data)

    def perform_update(self, serializer):
        obj = serializer.save()
        record_audit(self.request, "update", obj.module, obj.pk, obj.data)

    def perform_destroy(self, instance):
        record_audit(self.request, "delete", instance.module, instance.pk, instance.data)
        instance.delete()
