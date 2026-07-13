from datetime import date

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.tenants.mixins import TenantScopedMixin

from .models import PricingRule, best_price
from .serializers import PricingRuleSerializer


class PricingRuleViewSet(TenantScopedMixin, viewsets.ModelViewSet):
    queryset = PricingRule.objects.all()
    serializer_class = PricingRuleSerializer

    @action(detail=False, methods=["get"])
    def quote(self, request):
        """Best price for item_code/category/quantity/base_price."""
        p = request.query_params
        item_code = p.get("item_code", "")
        category = p.get("category", "")
        try:
            quantity = float(p.get("quantity", 1))
            base = float(p.get("base_price", 0))
        except ValueError:
            return Response({"error": "قيم غير صالحة"}, status=400)
        rules = list(self.get_queryset().filter(is_active=True))
        final, rule = best_price(rules, item_code, category, quantity, base, date.today())
        return Response({
            "base_price": base,
            "final_price": float(final),
            "discount": round(base - float(final), 2),
            "applied_rule": rule.name if rule else None,
        })
