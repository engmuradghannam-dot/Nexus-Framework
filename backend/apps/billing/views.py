from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Plan, Subscription, Invoice, Payment, UsageRecord
from .serializers import (
    PlanSerializer, SubscriptionSerializer, InvoiceSerializer,
    PaymentSerializer, CheckoutSessionSerializer
)
from .stripe_service import StripeService


class PlanViewSet(viewsets.ReadOnlyModelViewSet):
    """Public plan listing."""
    queryset = Plan.objects.filter(is_active=True, is_public=True)
    serializer_class = PlanSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'code'


class SubscriptionViewSet(viewsets.ModelViewSet):
    """Subscription management for authenticated tenant users."""
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if hasattr(self.request, 'tenant'):
            return Subscription.objects.filter(tenant_id=self.request.tenant['id'])
        return Subscription.objects.none()

    @action(detail=False, methods=['post'])
    def checkout(self, request):
        """Create Stripe checkout session for plan upgrade."""
        serializer = CheckoutSessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        plan_id = serializer.validated_data['plan_id']
        try:
            plan = Plan.objects.get(id=plan_id, is_active=True)
        except Plan.DoesNotExist:
            return Response({'error': 'Plan not found'}, status=404)

        tenant = request.tenant  # From middleware
        stripe_service = StripeService()

        session = stripe_service.create_checkout_session(
            tenant=tenant,
            plan=plan,
            success_url=serializer.validated_data['success_url'],
            cancel_url=serializer.validated_data['cancel_url'],
            interval=serializer.validated_data.get('billing_interval', 'month')
        )

        return Response({'session_id': session.id, 'url': session.url})

    @action(detail=False, methods=['post'])
    def cancel(self, request):
        """Cancel subscription at period end."""
        tenant_id = request.tenant['id']
        try:
            sub = Subscription.objects.get(tenant_id=tenant_id)
            if not sub.can_cancel():
                return Response({'error': 'Subscription cannot be cancelled'}, status=400)

            stripe_service = StripeService()
            stripe_service.cancel_subscription(sub.stripe_subscription_id)

            sub.cancel_at_period_end = True
            sub.canceled_at = timezone.now()
            sub.save()

            return Response({'status': 'cancelled', 'effective_date': sub.current_period_end})
        except Subscription.DoesNotExist:
            return Response({'error': 'No active subscription'}, status=404)

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current tenant subscription."""
        tenant_id = request.tenant['id']
        try:
            sub = Subscription.objects.select_related('plan').get(tenant_id=tenant_id)
            serializer = SubscriptionSerializer(sub)
            return Response(serializer.data)
        except Subscription.DoesNotExist:
            return Response({'error': 'No subscription found'}, status=404)


class InvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    """Invoice history for tenant."""
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if hasattr(self.request, 'tenant'):
            return Invoice.objects.filter(tenant_id=self.request.tenant['id'])
        return Invoice.objects.none()


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """Payment history for tenant."""
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if hasattr(self.request, 'tenant'):
            return Payment.objects.filter(tenant_id=self.request.tenant['id'])
        return Payment.objects.none()


class WebhookViewSet(viewsets.ViewSet):
    """Stripe webhook handler."""
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    @action(detail=False, methods=['post'], url_path='webhook')
    def stripe_webhook(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

        stripe_service = StripeService()
        success, result = stripe_service.handle_webhook(payload, sig_header)

        if not success:
            return Response({'error': result}, status=400)

        return Response({'status': 'ok', 'event': result})
