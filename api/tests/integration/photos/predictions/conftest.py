import pytest

from tigaserver_app.models import PhotoPrediction

from .factories import create_photo_prediction

# NOTE: needed for token with perms fixture
@pytest.fixture
def model_class():
    return PhotoPrediction

@pytest.fixture
def endpoint(report_photo):
    return f"photos/{report_photo.uuid}/prediction"

@pytest.fixture
def photo_prediction(report_photo):
    return create_photo_prediction(photo=report_photo)
