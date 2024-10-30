import pytest

from tigaserver_app.models import Photo


# NOTE: needed for token with perms fixture
@pytest.fixture
def model_class():
    return Photo
