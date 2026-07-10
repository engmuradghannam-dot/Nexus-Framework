import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.core.models import Branch, User, Warehouse


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
    branch = Branch.objects.create(name="HQ", code="HQ-001", address="Main St")
    wh = Warehouse.objects.create(
        name="Main WH",
        code="WH-001",
        branch=branch,
        capacity=1000,
        current_occupancy=750,
    )
    assert wh.occupancy_rate == 75.00


@pytest.mark.django_db
def test_api_branches_list(api_client, superuser):
    api_client.force_authenticate(user=superuser)
    Branch.objects.create(name="HQ", code="HQ-001", address="Main St")
    response = api_client.get("/api/core/branches/")
    assert response.status_code == 200
    assert len(response.data["results"]) == 1
