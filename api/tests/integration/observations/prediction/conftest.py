import pytest

from tigaserver_app.models import ObservationPrediction

from ...photos.predictions.factories import create_photo_prediction

from .factories import create_observation_prediction


# NOTE: needed for token with perms fixture
@pytest.fixture
def model_class():
    return ObservationPrediction

@pytest.fixture
def endpoint(published_observation_with_photo):
    return f"observations/{published_observation_with_photo.pk}/prediction"

@pytest.fixture
def published_observation_photo_with_prediction(published_observation_photo):
    _ = create_photo_prediction(photo=published_observation_photo)
    return published_observation_photo

@pytest.fixture
def published_observation_with_prediction(published_observation_photo_with_prediction):
    _ = create_observation_prediction(photo_prediction=published_observation_photo_with_prediction.prediction)
    return published_observation_photo_with_prediction
