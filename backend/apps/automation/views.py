from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.tenants.mixins import TenantScopedMixin

from .models import ScheduledJob, Webhook, WebhookDelivery
from .serializers import (ScheduledJobSerializer, WebhookDeliverySerializer,
                          WebhookSerializer)


class ScheduledJobViewSet(TenantScopedMixin, viewsets.ModelViewSet):
    queryset = ScheduledJob.objects.all()
    serializer_class = ScheduledJobSerializer

    @action(detail=True, methods=["post"])
    def run(self, request, pk=None):
        job = self.get_object()
        msg = job.run_now()
        return Response({"success": True, "message": msg, "job": self.get_serializer(job).data})


class WebhookViewSet(TenantScopedMixin, viewsets.ModelViewSet):
    queryset = Webhook.objects.all()
    serializer_class = WebhookSerializer

    @action(detail=True, methods=["post"])
    def trigger(self, request, pk=None):
        webhook = self.get_object()
        delivery = webhook.deliver(request.data.get("payload"))
        return Response({"success": delivery.status == "success", "status": delivery.status,
                         "status_code": delivery.status_code, "error": delivery.error,
                         "delivery": WebhookDeliverySerializer(delivery).data})


class WebhookDeliveryViewSet(TenantScopedMixin, viewsets.ReadOnlyModelViewSet):
    queryset = WebhookDelivery.objects.all()
    serializer_class = WebhookDeliverySerializer

    def get_queryset(self):
        qs = super().get_queryset()
        wh = self.request.query_params.get("webhook")
        return qs.filter(webhook=wh) if wh else qs
