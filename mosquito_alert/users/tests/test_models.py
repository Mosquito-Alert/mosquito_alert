import pytest

from mosquito_alert.users.models import UserStat

from .factories import UserFactory


@pytest.mark.django_db
class TestUserModel:
    def test_userstat_is_created_on_user_creation(self):
        user = UserFactory()
        assert UserStat.objects.filter(user=user).exists()
