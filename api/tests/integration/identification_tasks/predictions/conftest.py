import pytest

from tigacrafting.models import PhotoPrediction

from .factories import create_photo_prediction

# NOTE: needed for token with perms fixture
@pytest.fixture
def model_class():
    return PhotoPrediction

@pytest.fixture
def endpoint(identification_task):
    return f"identification-tasks/{identification_task.pk}/predictions"

@pytest.fixture
def photo_prediction(identification_task):
    return create_photo_prediction(photo=identification_task.photo)
