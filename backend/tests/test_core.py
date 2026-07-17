import pytest
from rest_framework.test import APIClient

from apps.core.models import Branch, CompanyProfile, User, Warehouse
from apps.tenants.models import Tenant


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def superuser():
    user = User.objects.create_superuser(
        email="eng.murad.ghannam@gmail.com", username="murad", password="ghannam2020"
    )
    user.permissions_level = 5
    user.save()
    return user


@pytest.mark.django_db
def test_user_creation(superuser):
    assert superuser.email == "eng.murad.ghannam@gmail.com"
    assert superuser.is_superuser
    assert superuser.permissions_level == 5


@pytest.mark.django_db
def test_branch_creation():
    branch = Branch.objects.create(
        name="Test Branch",
        code="TST-001",
        address="123 Test St",
        latitude=25.2048,
        longitude=55.2708,
    )
    assert branch.code == "TST-001"
    assert branch.latitude == 25.2048


@pytest.mark.django_db
def test_warehouse_occupancy():
    """occupancy_rate derives from the stock ledger.

    It used to divide the hand-entered `current_occupancy` field by capacity.
    Nothing in the system ever wrote that field, so the rate reported whatever
    someone last typed — and WHS-CTRL-002's 90% alert was built on it.
    """
    from apps.core.models import CompanyProfile
    from apps.inventory.models import Item, StockEntry

    company = CompanyProfile.objects.create(name="Occ Co", code="OCC-CO")
    branch = Branch.objects.create(company=company, name="HQ", code="HQ-001", address="Main St")
    wh = Warehouse.objects.create(
        name="Main WH", code="WH-001", branch=branch, capacity=1000,
    )
    item = Item.objects.create(company=company, item_code="OCC-1", item_name="Box")

    assert wh.occupancy_rate == 0
    StockEntry.objects.create(
        company=company, warehouse=wh, item=item, entry_type="Receipt", quantity=750, rate=1
    )
    assert wh.occupancy_rate == 75.00
    assert wh.is_near_capacity is False

    StockEntry.objects.create(
        company=company, warehouse=wh, item=item, entry_type="Receipt", quantity=200, rate=1
    )
    assert wh.occupancy_rate == 95.00
    assert wh.is_near_capacity is True  # WHS-CTRL-002


@pytest.mark.django_db
def test_warehouse_occupancy_ignores_the_legacy_manual_field():
    """current_occupancy is retained for API/admin backward compatibility but no
    longer drives the rate — otherwise a stale hand-typed number silences the
    capacity alert."""
    from apps.core.models import CompanyProfile

    company = CompanyProfile.objects.create(name="Legacy Co", code="LEG-CO")
    branch = Branch.objects.create(company=company, name="HQ", code="HQ-L", address="Main St")
    wh = Warehouse.objects.create(
        name="Legacy WH", code="WH-L", branch=branch, capacity=1000, current_occupancy=750,
    )
    assert wh.occupancy_rate == 0


@pytest.mark.django_db
def test_api_branches_list(api_client, superuser):
    api_client.force_authenticate(user=superuser)
    Branch.objects.create(name="HQ", code="HQ-001", address="Main St")
    response = api_client.get("/api/core/branches/")
    assert response.status_code == 200
    assert len(response.data["results"]) == 1


@pytest.mark.django_db
class TestCompanyProfileScoping:
    def test_unrelated_user_cannot_see_or_take_over_company(self, api_client):
        owner = User.objects.create_user(
            username="owner", email="owner@x.com", password="pw12345678"
        )
        outsider = User.objects.create_user(
            username="outsider", email="outsider@x.com", password="pw12345678"
        )
        company = CompanyProfile.objects.create(
            name="Secret Co", code="SEC1", super_admin=owner
        )

        api_client.force_authenticate(user=outsider)
        # Can't see a company they don't manage.
        res = api_client.get("/api/core/companies/")
        assert res.status_code == 200
        assert res.data["count"] == 0

        # Can't take it over by writing themselves in as super_admin.
        res = api_client.patch(
            f"/api/core/companies/{company.id}/", {"super_admin": str(outsider.id)}
        )
        assert res.status_code == 403
        company.refresh_from_db()
        assert company.super_admin_id == owner.id

    def test_owner_sees_own_company(self, api_client):
        owner = User.objects.create_user(
            username="owner2", email="owner2@x.com", password="pw12345678"
        )
        CompanyProfile.objects.create(name="Owned Co", code="OWN1", super_admin=owner)

        api_client.force_authenticate(user=owner)
        res = api_client.get("/api/core/companies/")
        assert res.status_code == 200
        assert res.data["count"] == 1

    def test_non_superuser_cannot_create_company(self, api_client):
        user = User.objects.create_user(
            username="creator", email="creator@x.com", password="pw12345678"
        )
        api_client.force_authenticate(user=user)
        res = api_client.post(
            "/api/core/companies/", {"name": "New Co", "code": "NEW1"}
        )
        assert res.status_code == 403


@pytest.mark.django_db
class TestUserViewSetPrivilegeEscalation:
    def test_user_cannot_self_promote_permissions_level(self, api_client):
        user = User.objects.create_user(
            username="climber", email="climber@x.com", password="pw12345678"
        )
        api_client.force_authenticate(user=user)
        res = api_client.patch(f"/api/core/users/{user.id}/", {"permissions_level": 5})
        assert res.status_code == 200
        user.refresh_from_db()
        assert user.permissions_level == 1

    def test_user_cannot_deactivate_another_user(self, api_client):
        tenant = Tenant.objects.create(name="Acme", slug="acme")
        user = User.objects.create_user(
            username="attacker", email="attacker@x.com", password="pw12345678", tenant=tenant
        )
        victim = User.objects.create_user(
            username="victim", email="victim@x.com", password="pw12345678", tenant=tenant
        )
        api_client.force_authenticate(user=user)
        res = api_client.patch(f"/api/core/users/{victim.id}/", {"is_active": False})
        assert res.status_code == 403
        victim.refresh_from_db()
        assert victim.is_active is True

    def test_superuser_can_change_permissions_level(self, api_client):
        admin = User.objects.create_superuser(
            username="admin4", email="admin4@x.com", password="pw12345678"
        )
        target = User.objects.create_user(
            username="target", email="target@x.com", password="pw12345678"
        )
        api_client.force_authenticate(user=admin)
        res = api_client.patch(f"/api/core/users/{target.id}/", {"permissions_level": 4})
        assert res.status_code == 200
        target.refresh_from_db()
        assert target.permissions_level == 4
