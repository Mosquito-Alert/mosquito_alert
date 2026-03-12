import pytest

from mosquito_alert.tigaserver_app.models import EuropeCountry

# NOTE: needed for token with perms fixture
@pytest.fixture
def model_class():
    return EuropeCountry
