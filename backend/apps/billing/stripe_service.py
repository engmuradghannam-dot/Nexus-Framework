"""
Stripe integration service for SaaS billing.
"""
import stripe
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from .models import Plan, Subscription, Invoice, Payment


class StripeService:
    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    def create_customer(self, tenant, email=None, name=None):
        """Create Stripe customer for tenant."""
        customer = stripe.Customer.create(
            email=email or tenant.email,
            name=name or tenant.name,
            metadata={
                'tenant_id': str(tenant.id),
                'tenant_schema': tenant.schema_name,
            }
        )
        tenant.stripe_customer_id = customer.id
        tenant.save(update_fields=['stripe_customer_id'])
        return customer

    def create_subscription(self, tenant, plan, payment_method_id=None):
        """Create Stripe subscription with trial."""
        if not tenant.stripe_customer_id:
            self.create_customer(tenant)

        items = [{'price': plan.stripe_price_id}]

        subscription_data = {
            'customer': tenant.stripe_customer_id,
            'items': items,
            'trial_period_days': getattr(settings, 'SAAS_TRIAL_DAYS', 14),
            'metadata': {'tenant_id': str(tenant.id)},
        }

        if payment_method_id:
            subscription_data['default_payment_method'] = payment_method_id

        stripe_sub = stripe.Subscription.create(**subscription_data)

        sub = Subscription.objects.create(
            tenant=tenant,
            plan=plan,
            stripe_subscription_id=stripe_sub.id,
            stripe_customer_id=tenant.stripe_customer_id,
            status=stripe_sub.status,
            current_period_start=timezone.datetime.fromtimestamp(stripe_sub.current_period_start, tz=timezone.utc),
            current_period_end=timezone.datetime.fromtimestamp(stripe_sub.current_period_end, tz=timezone.utc),
            trial_start=timezone.datetime.fromtimestamp(stripe_sub.trial_start, tz=timezone.utc) if stripe_sub.trial_start else None,
            trial_end=timezone.datetime.fromtimestamp(stripe_sub.trial_end, tz=timezone.utc) if stripe_sub.trial_end else None,
        )

        return sub

    def create_checkout_session(self, tenant, plan, success_url, cancel_url, interval='month'):
        """Create Stripe checkout session for plan upgrade."""
        if not tenant.stripe_customer_id:
            self.create_customer(tenant)

        price_id = plan.stripe_price_id

        session = stripe.checkout.Session.create(
            customer=tenant.stripe_customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={'tenant_id': str(tenant.id), 'plan_id': str(plan.id)},
        )
        return session

    def cancel_subscription(self, stripe_subscription_id):
        """Cancel subscription in Stripe."""
        return stripe.Subscription.delete(stripe_subscription_id)

    def handle_webhook(self, payload, sig_header):
        """Process Stripe webhook events."""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )
        except ValueError:
            return False, "Invalid payload"
        except stripe.error.SignatureVerificationError:
            return False, "Invalid signature"

        handlers = {
            'invoice.payment_succeeded': self._on_payment_succeeded,
            'invoice.payment_failed': self._on_payment_failed,
            'customer.subscription.updated': self._on_subscription_updated,
            'customer.subscription.deleted': self._on_subscription_deleted,
            'checkout.session.completed': self._on_checkout_completed,
        }

        handler = handlers.get(event['type'])
        if handler:
            handler(event['data']['object'])

        return True, event['type']

    def _on_payment_succeeded(self, invoice_data):
        stripe_sub_id = invoice_data.get('subscription')
        try:
            sub = Subscription.objects.get(stripe_subscription_id=stripe_sub_id)
            sub.status = 'active'
            sub.save()

            Invoice.objects.update_or_create(
                stripe_invoice_id=invoice_data['id'],
                defaults={
                    'tenant': sub.tenant,
                    'subscription': sub,
                    'status': 'paid',
                    'subtotal': Decimal(invoice_data['amount_due']) / 100,
                    'total': Decimal(invoice_data['amount_due']) / 100,
                    'amount_paid': Decimal(invoice_data['amount_paid']) / 100,
                    'amount_due': 0,
                    'paid_at': timezone.now(),
                }
            )
        except Subscription.DoesNotExist:
            pass

    def _on_payment_failed(self, invoice_data):
        stripe_sub_id = invoice_data.get('subscription')
        Subscription.objects.filter(stripe_subscription_id=stripe_sub_id).update(status='past_due')

    def _on_subscription_updated(self, sub_data):
        Subscription.objects.filter(stripe_subscription_id=sub_data['id']).update(
            status=sub_data['status'],
            cancel_at_period_end=sub_data['cancel_at_period_end'],
            current_period_end=timezone.datetime.fromtimestamp(sub_data['current_period_end'], tz=timezone.utc),
        )

    def _on_subscription_deleted(self, sub_data):
        Subscription.objects.filter(stripe_subscription_id=sub_data['id']).update(
            status='canceled',
            canceled_at=timezone.now()
        )

    def _on_checkout_completed(self, session_data):
        """Handle successful checkout."""
        tenant_id = session_data.get('metadata', {}).get('tenant_id')
        plan_id = session_data.get('metadata', {}).get('plan_id')
        if tenant_id and plan_id:
            from tenants.models import Tenant
            try:
                tenant = Tenant.objects.get(id=tenant_id)
                plan = Plan.objects.get(id=plan_id)
                # Update tenant tier
                tenant.tier = plan.tier
                tenant.status = 'active'
                tenant.save()
            except (Tenant.DoesNotExist, Plan.DoesNotExist):
                pass
