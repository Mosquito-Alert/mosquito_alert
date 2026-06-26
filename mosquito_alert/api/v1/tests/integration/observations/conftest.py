from datetime import timedelta
import pytest

from mosquito_alert.reports.models import Report
from mosquito_alert.reports.tests.factories import (
    ObservationReportFactory,
    PhotoFactory,
)


# NOTE: needed for token with perms fixture
@pytest.fixture
def model_class():
    return Report


@pytest.fixture()
def object(app_user):
    return ObservationReportFactory(user=app_user)


@pytest.fixture
def published_object(app_user):
    observation_obj = ObservationReportFactory(user=app_user)
    observation_obj.published_at = observation_obj.server_upload_time
    observation_obj.save()
    return observation_obj


@pytest.fixture
def published_object_30_days_ago(app_user, published_object):
    observation_obj = ObservationReportFactory(
        user=app_user,
        creation_time=published_object.creation_time - timedelta(days=30),
    )
    observation_obj.published_at = observation_obj.server_upload_time
    observation_obj.save()
    return observation_obj


@pytest.fixture
def published_object_in_10km(app_user, published_object):
    p = published_object.point.clone()
    p.transform(3857)  # transform to meters
    p.x += 10_000  # ~10km east of the default location
    p.transform(4326)  # transform back to lat/lon

    observation_obj = ObservationReportFactory(user=app_user, point=p)
    observation_obj.published_at = observation_obj.server_upload_time
    observation_obj.save()
    return observation_obj


@pytest.fixture
def published_object_in_100km(app_user, published_object):
    p = published_object.point.clone()
    p.transform(3857)  # transform to meters
    p.x += 100_000  # ~100km east of the default location
    p.transform(4326)  # transform back to lat/lon

    observation_obj = ObservationReportFactory(
        user=app_user,
        point=p,
    )
    observation_obj.published_at = observation_obj.server_upload_time
    observation_obj.save()
    return observation_obj


@pytest.fixture
def unpublished_object(app_user):
    return ObservationReportFactory(user=app_user, published_at=None)


@pytest.fixture
def soft_deleted_object(app_user):
    observation_obj = ObservationReportFactory(user=app_user)
    observation_obj.soft_delete()

    return observation_obj


@pytest.fixture
def published_observation_with_photo(app_user):
    observation_obj = ObservationReportFactory(user=app_user)
    observation_obj.published_at = observation_obj.server_upload_time
    observation_obj.save()
    return observation_obj


@pytest.fixture
def published_observation_without_photo(app_user):
    observation_obj = ObservationReportFactory(user=app_user, photos=[])
    observation_obj.published_at = observation_obj.server_upload_time
    observation_obj.save()
    return observation_obj


@pytest.fixture
def hidden_photo():
    return PhotoFactory.build(hide=True)


@pytest.fixture
def published_observation_with_hidden_photo(
    published_observation_with_photo, hidden_photo
):
    hidden_photo.report = published_observation_with_photo
    hidden_photo.save()
    return published_observation_with_photo
