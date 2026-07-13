from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.tenants.mixins import TenantScopedMixin

from .models import NotificationLog, NotificationTemplate, deliver
from .serializers import NotificationLogSerializer, NotificationTemplateSerializer


class NotificationTemplateViewSet(TenantScopedMixin, viewsets.ModelViewSet):
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer

    @action(detail=True, methods=["post"])
    def send(self, request, pk=None):
        tpl = self.get_object()
        recipient = request.data.get("recipient", "")
        if not recipient:
            return Response({"success": False, "message": "المستلم مطلوب"}, status=400)
        subject, body = tpl.render(request.data.get("context", {}))
        log = deliver(tpl.channel, recipient, subject, body, tenant=getattr(request.user, "tenant", None))
        return Response({"success": True, "status": log.status,
                         "message": f"البريد" if tpl.channel == "email" else "الرسالة",
                         "log": NotificationLogSerializer(log).data})


class NotificationLogViewSet(TenantScopedMixin, viewsets.ReadOnlyModelViewSet):
    queryset = NotificationLog.objects.all()
    serializer_class = NotificationLogSerializer
