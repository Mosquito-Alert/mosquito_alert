import pytest

from mosquito_alert.geo.models import EuropeCountry


# NOTE: needed for token with perms fixture
@pytest.fixture
def model_class():
    return EuropeCountry
