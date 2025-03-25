import pytest

from tigacrafting.models import IdentificationTask
from tigaserver_app.models import Photo

from ..observations.factories import create_observation_object
from .predictions.factories import create_photo_prediction

# NOTE: needed for token with perms fixture
@pytest.fixture
def model_class():
    return IdentificationTask

@pytest.fixture
def identification_task_fully_predicted(app_user, dummy_image):
    observation = create_observation_object(user=app_user)
    photo = Photo.objects.create(
        photo=dummy_image,
        report=observation,
    )
    create_photo_prediction(photo=photo)

    return observation.identification_task

@pytest.fixture
def identification_task_with_pending_predictions(app_user, dummy_image):
    observation = create_observation_object(user=app_user)
    photo = Photo.objects.create(
        photo=dummy_image,
        report=observation,
    )
    create_photo_prediction(photo=photo)
    _ = Photo.objects.create(
        photo=dummy_image,
        report=observation,
    )

    return observation.identification_task