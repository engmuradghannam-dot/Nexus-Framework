import pytest

from nexus.apps.audit.models import ChangeHeader
from nexus.apps.industry.models import Product


@pytest.mark.django_db
def test_create_logs_insert_header_and_items():
    # CDHDR/CDPOS: creating a tracked model logs an 'I' header with field items
    product = Product.objects.create(name='Widget', sku='AUD-001', unit_price=15)

    from django.contrib.contenttypes.models import ContentType
    content_type = ContentType.objects.get_for_model(Product)
    header = ChangeHeader.objects.get(content_type=content_type, object_id=str(product.pk), change_type='I')
    field_names = set(header.items.values_list('field_name', flat=True))
    assert 'sku' in field_names
    assert 'unit_price' in field_names


@pytest.mark.django_db
def test_update_logs_only_changed_fields():
    product = Product.objects.create(name='Widget', sku='AUD-002', unit_price=15)

    product.unit_price = 25
    product.save()

    from django.contrib.contenttypes.models import ContentType
    content_type = ContentType.objects.get_for_model(Product)
    header = ChangeHeader.objects.filter(content_type=content_type, object_id=str(product.pk), change_type='U').latest('change_time')
    items = list(header.items.all())
    assert len(items) == 1
    item = items[0]
    assert item.field_name == 'unit_price'
    assert item.value_old == '15.00'
    assert item.value_new == '25.00'


@pytest.mark.django_db
def test_delete_logs_full_snapshot():
    product = Product.objects.create(name='Widget', sku='AUD-003', unit_price=15)
    pk = product.pk
    product.delete()

    from django.contrib.contenttypes.models import ContentType
    content_type = ContentType.objects.get_for_model(Product)
    header = ChangeHeader.objects.get(content_type=content_type, object_id=str(pk), change_type='D')
    field_names = set(header.items.values_list('field_name', flat=True))
    assert 'sku' in field_names


@pytest.mark.django_db
def test_untracked_field_change_produces_no_header():
    # Company is not in the audited model registry
    from nexus.apps.core.models import Company
    before_count = ChangeHeader.objects.count()
    Company.objects.create(name='Untracked Co')
    assert ChangeHeader.objects.count() == before_count
