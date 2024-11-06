import pytest

from tigapublic.models import MapAuxReports
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

    _ = MapAuxReports.objects.get_or_create(
        version_uuid=breeding_site_obj,
        defaults={
            "id": 10,
            "user_id": breeding_site_obj.user.pk,
            "ref_system": 4326,
            "type": breeding_site_obj.type,
            "final_expert_status": 1,
            "visible": True,
        },
    )
    return breeding_site_obj

@pytest.fixture
def unpublished_object(app_user):
    breeding_site_obj = create_breeding_site_object(user=app_user)

    _ = MapAuxReports.objects.filter(version_uuid=breeding_site_obj).delete()
    return breeding_site_obj

@pytest.fixture
def soft_deleted_object(app_user):
    breeding_site_obj = create_breeding_site_object(user=app_user)
    breeding_site_obj.soft_delete()

    return breeding_site_obj
