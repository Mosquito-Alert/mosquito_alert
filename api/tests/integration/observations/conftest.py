import pytest

from tigaserver_app.models import Report, Photo

from api.tests.integration.photos.predictions.factories import create_photo_prediction

from .prediction.factories import create_observation_prediction
from .factories import create_observation_object

# NOTE: needed for token with perms fixture
@pytest.fixture
def model_class():
    return Report

@pytest.fixture()
def object(app_user):
    return create_observation_object(user=app_user)

@pytest.fixture
def published_object(app_user):
    return create_observation_object(user=app_user, is_published=True)

@pytest.fixture
def unpublished_object(app_user):
    return create_observation_object(user=app_user, is_published=False)

@pytest.fixture
def soft_deleted_object(app_user):
    observation_obj = create_observation_object(user=app_user)
    observation_obj.soft_delete()

    return observation_obj

@pytest.fixture
def published_observation_with_photo(app_user, dummy_image):
    observation_obj = create_observation_object(user=app_user, is_published=True)

    _ = Photo.objects.create(
        photo=dummy_image,
        report=observation_obj,
    )

    return observation_obj

@pytest.fixture
def published_observation_photo(published_observation_with_photo):
    return published_observation_with_photo.photos.first()

@pytest.fixture
def hidden_photo(dummy_image):
    return Photo(photo=dummy_image, hide=True)

@pytest.fixture
def published_observation_with_hidden_photo(published_observation_with_photo, hidden_photo):
    hidden_photo.report=published_observation_with_photo
    hidden_photo.save()
    return published_observation_with_photo

@pytest.fixture
def published_observation_with_prediction(published_observation_with_photo):
    _ = create_observation_prediction(
        photo_prediction=create_photo_prediction(photo=published_observation_with_photo.photos.first())
    )
    return published_observation_with_photo

@pytest.fixture
def published_observation_with_pending_photo_prediction(published_observation_with_photo, dummy_image):
    create_photo_prediction(photo=published_observation_with_photo.photos.first())

    # Create new Photo object without assigning prediction
    _ = Photo.objects.create(
        photo=dummy_image,
        report=published_observation_with_photo,
    )

    return published_observation_with_photo