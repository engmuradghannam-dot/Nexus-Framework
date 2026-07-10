from decimal import Decimal

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import CountryTaxProfile, TaxCalculation, TaxRate, TaxRule
from .serializers import (
    CountryTaxProfileListSerializer,
    CountryTaxProfileSerializer,
    TaxCalculationCreateSerializer,
    TaxCalculationSerializer,
    TaxCalculatorInputSerializer,
    TaxCalculatorOutputSerializer,
    TaxRateSerializer,
    TaxRuleSerializer,
)


@extend_schema_view(
    list=extend_schema(tags=["Taxes"], summary="List country tax profiles"),
    retrieve=extend_schema(tags=["Taxes"], summary="Get country tax profile details"),
    create=extend_schema(tags=["Taxes"], summary="Create country tax profile"),
    update=extend_schema(tags=["Taxes"], summary="Update country tax profile"),
    destroy=extend_schema(tags=["Taxes"], summary="Delete country tax profile"),
)
class CountryTaxProfileViewSet(viewsets.ModelViewSet):
    queryset = CountryTaxProfile.objects.all().prefetch_related("tax_rates", "tax_rules")
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "list":
            return CountryTaxProfileListSerializer
        return CountryTaxProfileSerializer

    @extend_schema(tags=["Taxes"], summary="Get tax profile by country code")
    @action(detail=False, methods=["get"], url_path="by-code/(?P<code>[^/.]+)")
    def by_code(self, request, code=None):
        profile = get_object_or_404(CountryTaxProfile, country_code__iexact=code.upper())
        serializer = CountryTaxProfileSerializer(profile)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(tags=["Taxes"], summary="List tax rates"),
    retrieve=extend_schema(tags=["Taxes"], summary="Get tax rate details"),
    create=extend_schema(tags=["Taxes"], summary="Create tax rate"),
    update=extend_schema(tags=["Taxes"], summary="Update tax rate"),
    destroy=extend_schema(tags=["Taxes"], summary="Delete tax rate"),
)
class TaxRateViewSet(viewsets.ModelViewSet):
    queryset = TaxRate.objects.all().select_related("country")
    serializer_class = TaxRateSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["country", "tax_type", "is_active"]
    search_fields = ["name", "description"]


@extend_schema_view(
    list=extend_schema(tags=["Taxes"], summary="List tax rules"),
    retrieve=extend_schema(tags=["Taxes"], summary="Get tax rule details"),
    create=extend_schema(tags=["Taxes"], summary="Create tax rule"),
    update=extend_schema(tags=["Taxes"], summary="Update tax rule"),
    destroy=extend_schema(tags=["Taxes"], summary="Delete tax rule"),
)
class TaxRuleViewSet(viewsets.ModelViewSet):
    queryset = TaxRule.objects.all().select_related("country")
    serializer_class = TaxRuleSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["country", "rule_type", "is_active"]
    search_fields = ["name", "description"]


@extend_schema_view(
    list=extend_schema(tags=["Taxes"], summary="List tax calculations"),
    retrieve=extend_schema(tags=["Taxes"], summary="Get tax calculation details"),
    create=extend_schema(tags=["Taxes"], summary="Create tax calculation"),
)
class TaxCalculationViewSet(viewsets.ModelViewSet):
    queryset = TaxCalculation.objects.all().select_related("country")
    permission_classes = [IsAuthenticated]
    filterset_fields = ["country", "status", "is_b2b"]
    search_fields = ["reference_number", "customer_vat_id"]

    def get_serializer_class(self):
        if self.action in ["create", "update"]:
            return TaxCalculationCreateSerializer
        return TaxCalculationSerializer

    def create(self, request, *args, **kwargs):
        create_serializer = self.get_serializer(data=request.data)
        create_serializer.is_valid(raise_exception=True)
        calc = create_serializer.save()
        # Return the full representation including computed tax_amount/total_amount
        read_serializer = TaxCalculationSerializer(calc, context=self.get_serializer_context())
        headers = self.get_success_headers(read_serializer.data)
        return Response(
            read_serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    @extend_schema(
        tags=["Taxes"],
        summary="Calculate tax for a transaction",
        request=TaxCalculatorInputSerializer,
        responses={200: TaxCalculatorOutputSerializer},
    )
    @action(detail=False, methods=["post"])
    def calculate(self, request):
        input_serializer = TaxCalculatorInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        data = input_serializer.validated_data

        country = get_object_or_404(
            CountryTaxProfile, country_code__iexact=data["country_code"].upper(), is_active=True
        )

        calc = TaxCalculation(
            country=country,
            base_amount=data["amount"],
            is_b2b=data.get("is_b2b", False),
            customer_vat_id=data.get("customer_vat_id", ""),
            reference_number="CALC-" + str(Decimal(data["amount"]).quantize(Decimal("0.01"))),
        )
        calc.calculate()

        output = {
            "country_code": country.country_code,
            "base_amount": calc.base_amount,
            "tax_amount": calc.tax_amount,
            "total_amount": calc.total_amount,
            "applied_rates": calc.applied_tax_rates,
            "is_b2b": calc.is_b2b,
        }
        return Response(output, status=status.HTTP_200_OK)
