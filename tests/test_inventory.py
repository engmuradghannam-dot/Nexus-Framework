import pytest
from apps.inventory.models import Item, ItemGroup

@pytest.mark.django_db
class TestInventory:
    def test_create_item(self, company):
        group = ItemGroup.objects.create(company=company, name='Electronics')
        item = Item.objects.create(
            company=company, 
            item_code='LAPTOP-001', 
            item_name='Laptop', 
            item_group=group
        )
        assert item.item_code == 'LAPTOP-001'
        assert item.is_stock_item is True
