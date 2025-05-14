import pytest
import uuid

from django.contrib.auth import get_user_model

from tigaserver_app.models import TigaUser

from api.tests.utils import grant_permission_to_user

User = get_user_model()

# NOTE: needed for token with perms fixture
@pytest.fixture
def model_class():
    return TigaUser

@pytest.fixture
def user_uuid(user):
    return uuid.UUID(int=user.pk)

@pytest.fixture
def another_user_uuid(another_user):
    return uuid.UUID(int=another_user.pk)

@pytest.fixture
def perm_user_can_view_regular_user(user):
    return grant_permission_to_user(
        type="view", model_class=User, user=user
    )

@pytest.fixture
def jwt_token_user_can_view_regular_user(jwt_token_user, perm_user_can_view_regular_user):
    return jwt_token_user

@pytest.fixture
def perm_user_can_change_regular_user(user):
    return grant_permission_to_user(
        type="change", model_class=User, user=user
    )

@pytest.fixture
def jwt_token_user_can_change_regular_user(jwt_token_user, perm_user_can_change_regular_user):
    return jwt_token_user