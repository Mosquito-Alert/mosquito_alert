import pytest

from tigaserver_app.models import IAScore

from .factories import create_prediction

# NOTE: needed for token with perms fixture
@pytest.fixture
def model_class():
    return IAScore

@pytest.fixture
def endpoint(report_photo):
    return f"photos/{report_photo.uuid}/predictions"

@pytest.fixture
def albopictus_prediction(report_photo):
    return create_prediction(photo=report_photo)
