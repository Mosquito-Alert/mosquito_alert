import pytest

from mosquito_alert.notifications.models import Notification


# TODO: remove?
# NOTE: needed for token with perms fixture
@pytest.fixture
def model_class():
    return Notification