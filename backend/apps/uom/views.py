from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.tenants.mixins import TenantScopedMixin

from .models import (ItemVariant, UnitOfMeasure, UOMConversion, convert_uom,
                     generate_variants)
from .serializers import (ItemVariantSerializer, UnitOfMeasureSerializer,
                          UOMConversionSerializer)


class UnitOfMeasureViewSet(TenantScopedMixin, viewsets.ModelViewSet):
    queryset = UnitOfMeasure.objects.filter(is_active=True)
    serializer_class = UnitOfMeasureSerializer
    pagination_class = None

    @action(detail=False, methods=["get"])
    def convert(self, request):
        try:
            amount = float(request.query_params.get("amount", 0))
            f = UnitOfMeasure.objects.get(id=request.query_params.get("from"))
            t = UnitOfMeasure.objects.get(id=request.query_params.get("to"))
        except (ValueError, UnitOfMeasure.DoesNotExist):
            return Response({"error": "مدخلات غير صالحة"}, status=400)
        result = convert_uom(amount, f, t)
        if result is None:
            return Response({"success": False, "message": "لا توجد قاعدة تحويل"}, status=400)
        return Response({"success": True, "result": float(result), "from": f.code, "to": t.code})


class UOMConversionViewSet(TenantScopedMixin, viewsets.ModelViewSet):
    queryset = UOMConversion.objects.all()
    serializer_class = UOMConversionSerializer
    pagination_class = None


class ItemVariantViewSet(TenantScopedMixin, viewsets.ModelViewSet):
    queryset = ItemVariant.objects.all()
    serializer_class = ItemVariantSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        tc = self.request.query_params.get("template_code")
        return qs.filter(template_code=tc) if tc else qs

    @action(detail=False, methods=["post"])
    def generate(self, request):
        tc = request.data.get("template_code", "")
        name = request.data.get("template_name", "")
        attrs = request.data.get("attributes", {})
        if not tc or not attrs:
            return Response({"success": False, "message": "أدخل رمز الصنف والسمات"}, status=400)
        variants = generate_variants(tc, name, attrs, tenant=getattr(request.user, "tenant", None))
        return Response({"success": True, "count": len(variants),
                         "variants": ItemVariantSerializer(variants, many=True).data})
