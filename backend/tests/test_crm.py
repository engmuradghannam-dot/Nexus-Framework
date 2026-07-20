from decimal import Decimal

import pytest

from nexus.apps.core.models import Branch, Company
from nexus.apps.crm.models import Customer, CustomerInteraction, Opportunity


@pytest.fixture
def branch():
    company = Company.objects.create(name='Test Company')
    return Branch.objects.create(company=company, name='Main Branch')


@pytest.mark.django_db
def test_customer_id_auto_generated(branch):
    customer = Customer.objects.create(customer_name='Acme Corp', email='acme@test.com', phone='0500000000', branch=branch)
    assert customer.customer_id.startswith('CUST-')


@pytest.mark.django_db
def test_credit_limit_check(branch):
    # CRM-CTRL-001 / SAL-CTRL-001 Credit Limit Check
    customer = Customer.objects.create(
        customer_name='Acme Corp', email='acme2@test.com', phone='0500000001',
        branch=branch, credit_limit=Decimal('10000'),
    )
    assert customer.exceeds_credit_limit(5000) is False
    assert customer.exceeds_credit_limit(15000) is True


@pytest.mark.django_db
def test_duplicate_detection_by_email(branch):
    # CRM-CTRL-002 Duplicate Prevention
    Customer.objects.create(customer_name='Acme', email='dup@test.com', phone='0500000002', branch=branch)
    duplicates = Customer.find_duplicates(email='dup@test.com')
    assert duplicates.count() == 1


@pytest.mark.django_db
def test_lead_scoring(branch):
    # CRM-RULE-001 Lead Scoring
    customer = Customer.objects.create(customer_name='Beta LLC', email='beta@test.com', phone='0500000003', branch=branch)
    for _ in range(3):
        CustomerInteraction.objects.create(customer=customer, interaction_type='call')
    score = customer.calculate_score()
    assert score == 30


@pytest.mark.django_db
def test_clv_calculation(branch):
    # CRM-RULE-004 Customer Lifetime Value
    customer = Customer.objects.create(customer_name='Gamma Inc', email='gamma@test.com', phone='0500000004', branch=branch)
    clv = customer.calculate_clv(avg_order_value=1000, purchase_frequency_per_year=4, customer_lifespan_years=5)
    assert clv == Decimal('20000.00')


@pytest.mark.django_db
def test_tier_upgrade(branch):
    # SAL-RULE-005 Customer Tier Upgrade
    customer = Customer.objects.create(customer_name='Delta Co', email='delta@test.com', phone='0500000005', branch=branch)
    assert customer.tier == 'bronze'
    customer.maybe_upgrade_tier(Decimal('60000'))
    assert customer.tier == 'silver'


@pytest.mark.django_db
def test_opportunity_discount_approval(branch):
    # CRM-RULE-005 Discount Approval (> 10%)
    customer = Customer.objects.create(customer_name='Epsilon', email='epsilon@test.com', phone='0500000006', branch=branch)
    opportunity = Opportunity.objects.create(customer=customer, name='Big Deal', discount_pct=Decimal('15'))
    assert opportunity.requires_discount_approval is True


@pytest.mark.django_db
def test_opportunity_stage_transition_validation(branch):
    # CRM-RULE-002 Opportunity Stage Progression
    customer = Customer.objects.create(customer_name='Zeta', email='zeta@test.com', phone='0500000007', branch=branch)
    opportunity = Opportunity.objects.create(customer=customer, name='Deal', stage='qualification')
    assert opportunity.validate_stage_transition('proposal') is True
    assert opportunity.validate_stage_transition('qualification') is True
