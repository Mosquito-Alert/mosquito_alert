import pytest

from tigaserver_app.models import EuropeCountry

# NOTE: needed for token with perms fixture
@pytest.fixture
def model_class():
    return EuropeCountry
