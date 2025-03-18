import pytest

from tigaserver_app.models import Report

from .factories import create_breeding_site_object

# NOTE: needed for token with perms fixture
@pytest.fixture
def model_class():
    return Report

@pytest.fixture()
def object(app_user):
    return create_breeding_site_object(user=app_user)

@pytest.fixture
def published_object(app_user):
    breeding_site_obj = create_breeding_site_object(user=app_user)
    breeding_site_obj.published_at = breeding_site_obj.server_upload_time
    breeding_site_obj.save()

    return breeding_site_obj

@pytest.fixture
def unpublished_object(app_user):
    breeding_site_obj = create_breeding_site_object(user=app_user)
    breeding_site_obj.hide = True
    breeding_site_obj.save()

    return breeding_site_obj

@pytest.fixture
def soft_deleted_object(app_user):
    breeding_site_obj = create_breeding_site_object(user=app_user)
    breeding_site_obj.soft_delete()

    return breeding_site_obj
