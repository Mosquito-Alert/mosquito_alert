import pytest

from tigaserver_app.models import Device

from .factories import create_device

# NOTE: needed for token with perms fixture
@pytest.fixture
def model_class():
    return Device

@pytest.fixture
def device(app_user):
    return create_device(user=app_user)
