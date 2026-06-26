from datetime import timedelta
import pytest

from mosquito_alert.reports.models import Report
from mosquito_alert.reports.tests.factories import BreedingSiteReportFactory


# NOTE: needed for token with perms fixture
@pytest.fixture
def model_class():
    return Report


@pytest.fixture()
def object(app_user):
    return BreedingSiteReportFactory(user=app_user)


@pytest.fixture
def published_object(app_user):
    breeding_site_obj = BreedingSiteReportFactory(user=app_user)
    breeding_site_obj.published_at = breeding_site_obj.server_upload_time
    breeding_site_obj.save()

    return breeding_site_obj


@pytest.fixture
def published_object_30_days_ago(app_user, published_object):
    breeding_site_obj = BreedingSiteReportFactory(
        user=app_user, creation_time=published_object.creation_time - timedelta(days=30)
    )
    breeding_site_obj.published_at = breeding_site_obj.server_upload_time
    breeding_site_obj.save()

    return breeding_site_obj


@pytest.fixture
def published_object_in_10km(app_user, published_object):
    p = published_object.point.clone()
    p.transform(3857)  # transform to meters
    p.x += 10_000  # ~10km east of the default location
    p.transform(4326)  # transform back to lat/lon

    breeding_site_obj = BreedingSiteReportFactory(user=app_user, point=p)
    breeding_site_obj.published_at = breeding_site_obj.server_upload_time
    breeding_site_obj.save()

    return breeding_site_obj


@pytest.fixture
def published_object_in_100km(app_user, published_object):
    p = published_object.point.clone()
    p.transform(3857)  # transform to meters
    p.x += 100_000  # ~100km east of the default location
    p.transform(4326)  # transform back to lat/lon

    breeding_site_obj = BreedingSiteReportFactory(user=app_user, point=p)
    breeding_site_obj.published_at = breeding_site_obj.server_upload_time
    breeding_site_obj.save()

    return breeding_site_obj


@pytest.fixture
def unpublished_object(app_user):
    breeding_site_obj = BreedingSiteReportFactory(user=app_user)
    breeding_site_obj.published_at = None
    breeding_site_obj.save()

    return breeding_site_obj


@pytest.fixture
def soft_deleted_object(app_user):
    breeding_site_obj = BreedingSiteReportFactory(user=app_user)
    breeding_site_obj.soft_delete()

    return breeding_site_obj
