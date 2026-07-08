import pytest
from apps.regulatory.models import Risk
from apps.core.models import User


@pytest.mark.django_db
def test_risk_score_calculation():
    user = User.objects.create_user(email='risk@test.com', username='risk', password='test')
    risk = Risk.objects.create(
        title='Data Breach', description='Potential leak',
        likelihood=4, impact=5, owner=user
    )
    assert risk.risk_score == 20
    assert risk.risk_level == 'Critical'
