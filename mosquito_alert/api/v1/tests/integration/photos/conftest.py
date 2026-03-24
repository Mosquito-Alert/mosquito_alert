import pytest

from mosquito_alert.reports.models import Photo


# NOTE: needed for token with perms fixture
@pytest.fixture
def model_class():
    return Photo
