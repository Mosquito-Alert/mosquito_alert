import pytest

from mosquito_alert.geo.models import Country


# NOTE: needed for token with perms fixture
@pytest.fixture
def model_class():
    return Country
