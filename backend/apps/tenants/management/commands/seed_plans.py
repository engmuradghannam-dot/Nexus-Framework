"""
Management command to seed default subscription plans.
"""
from django.core.management.base import BaseCommand
from apps.billing.models import Plan


class Command(BaseCommand):
    help = 'Seed default subscription plans'

    def handle(self, *args, **options):
        plans = [
            {
                'name': 'Free',
                'code': 'free',
                'description': 'Basic features for small teams',
                'tier': 'free',
                'price_monthly': 0,
                'price_yearly': 0,
                'max_users': 3,
                'max_warehouses': 1,
                'max_branches': 1,
                'storage_limit_gb': 1,
                'includes_api_access': False,
                'includes_advanced_reporting': False,
                'includes_ai_features': False,
                'includes_white_label': False,
                'enabled_modules': ['core', 'accounts', 'inventory'],
                'is_public': True,
                'sort_order': 1,
            },
            {
                'name': 'Starter',
                'code': 'starter',
                'description': 'Essential ERP features for growing businesses',
                'tier': 'starter',
                'price_monthly': 49,
                'price_yearly': 490,
                'max_users': 10,
                'max_warehouses': 3,
                'max_branches': 2,
                'storage_limit_gb': 10,
                'includes_api_access': True,
                'includes_advanced_reporting': False,
                'includes_ai_features': False,
                'includes_white_label': False,
                'enabled_modules': ['core', 'accounts', 'inventory', 'buying', 'selling', 'hr'],
                'is_public': True,
                'sort_order': 2,
            },
            {
                'name': 'Professional',
                'code': 'professional',
                'description': 'Advanced features with AI and analytics',
                'tier': 'professional',
                'price_monthly': 149,
                'price_yearly': 1490,
                'max_users': 50,
                'max_warehouses': 10,
                'max_branches': 5,
                'storage_limit_gb': 50,
                'includes_api_access': True,
                'includes_advanced_reporting': True,
                'includes_ai_features': True,
                'includes_white_label': False,
                'enabled_modules': ['core', 'accounts', 'inventory', 'buying', 'selling', 'manufacturing', 'hr', 'crm', 'projects', 'assets'],
                'is_public': True,
                'sort_order': 3,
            },
            {
                'name': 'Enterprise',
                'code': 'enterprise',
                'description': 'Full features with white-label and unlimited scale',
                'tier': 'enterprise',
                'price_monthly': 499,
                'price_yearly': 4990,
                'max_users': 999,
                'max_warehouses': 999,
                'max_branches': 999,
                'storage_limit_gb': 500,
                'includes_api_access': True,
                'includes_advanced_reporting': True,
                'includes_ai_features': True,
                'includes_white_label': True,
                'enabled_modules': ['core', 'accounts', 'inventory', 'buying', 'selling', 'manufacturing', 'hr', 'crm', 'projects', 'assets', 'workflow'],
                'is_public': True,
                'sort_order': 4,
            },
        ]

        for plan_data in plans:
            Plan.objects.update_or_create(
                code=plan_data['code'],
                defaults=plan_data
            )
            self.stdout.write(self.style.SUCCESS(f"Seeded plan: {plan_data['name']}"))

        self.stdout.write(self.style.SUCCESS('All plans seeded!'))
