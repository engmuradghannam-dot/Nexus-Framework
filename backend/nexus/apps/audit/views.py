from django.contrib.contenttypes.models import ContentType
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from .models import ChangeHeader
from .serializers import ChangeHeaderSerializer


class ChangeHeaderViewSet(viewsets.ReadOnlyModelViewSet):
    """CDHDR/CDPOS-style audit trail - read-only, changes are only ever
    written by the audit signal handlers.

    Every audited model is tracked centrally here regardless of which
    company/tenant it belongs to (see api_infra.tenancy_router.SHARED_APPS),
    and old/new field values routinely include sensitive data (salaries,
    invoice amounts, etc.). ChangeHeader reaches its target only through a
    generic content_type/object_id pair, and different audited models are
    company-scoped through different, model-specific paths (or not at all),
    so there's no single field to filter this queryset by company the way
    CompanyScopedViewSet does elsewhere. Until that per-model scoping is
    built, restrict this to staff - matching how SAP itself gates CDHDR/
    CDPOS access to auditors/admins, not every user - rather than leaving it
    open to any authenticated account.
    """

    queryset = ChangeHeader.objects.select_related('content_type', 'changed_by').prefetch_related('items').all()
    serializer_class = ChangeHeaderSerializer
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=['get'])
    def for_object(self, request):
        app_label = request.query_params.get('app_label')
        model = request.query_params.get('model')
        object_id = request.query_params.get('object_id')
        if not (app_label and model and object_id):
            return Response({"error": "app_label, model and object_id are required"}, status=status.HTTP_400_BAD_REQUEST)
        content_type = ContentType.objects.filter(app_label=app_label, model=model).first()
        if not content_type:
            return Response({"error": "unknown content type"}, status=status.HTTP_404_NOT_FOUND)
        headers = self.get_queryset().filter(content_type=content_type, object_id=str(object_id))
        serializer = self.get_serializer(headers, many=True)
        return Response(serializer.data)
