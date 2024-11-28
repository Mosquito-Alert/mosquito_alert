import pytest

from tigaserver_app.models import Device


# NOTE: needed for token with perms fixture
@pytest.fixture
def model_class():
    return Device

@pytest.fixture
def device(app_user):
    return Device.objects.create(
        device_id='unique_id',
        user=app_user,
        type='android',
        model='test_model',
        os_name='android',
        os_version='32'
    )