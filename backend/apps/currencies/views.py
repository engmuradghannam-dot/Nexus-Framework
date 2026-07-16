from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from .models import Currency, convert
from .serializers import CurrencySerializer


class CurrencyViewSet(viewsets.ModelViewSet):
    """FX rates are shared reference data used by every tenant's invoicing/
    FX gain-loss calculations — reading is open, editing rate_to_base
    requires a superuser."""

    queryset = Currency.objects.filter(is_active=True)
    serializer_class = CurrencySerializer
    pagination_class = None

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAdminUser()]
        return super().get_permissions()

    @action(detail=False, methods=["get"])
    def convert(self, request):
        amount = request.query_params.get("amount", 0)
        frm = request.query_params.get("from", "SAR")
        to = request.query_params.get("to", "SAR")
        result = convert(amount, frm, to)
        if result is None:
            return Response({"success": False, "message": "عملة غير معروفة"}, status=400)
        return Response({"success": True, "amount": float(amount), "from": frm, "to": to, "result": float(result)})
