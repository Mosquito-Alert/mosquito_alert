import pytest

from mosquito_alert.reports.models import Report

from .factories import create_bite_object


# NOTE: needed for token with perms fixture
@pytest.fixture
def model_class():
    return Report


@pytest.fixture()
def object(app_user):
    return create_bite_object(user=app_user)


@pytest.fixture
def published_object(app_user):
    bite_obj = create_bite_object(user=app_user)
    bite_obj.published_at = bite_obj.server_upload_time
    bite_obj.save()

    return bite_obj


@pytest.fixture
def published_object_in_10km(app_user):
    bite_obj = create_bite_object(user=app_user)
    bite_obj.published_at = bite_obj.server_upload_time
    bite_obj.current_location_lon += 0.09  # ~10km east of the default location
    bite_obj.save()

    return bite_obj


@pytest.fixture
def published_object_in_100km(app_user):
    bite_obj = create_bite_object(user=app_user)
    bite_obj.published_at = bite_obj.server_upload_time
    bite_obj.current_location_lon += 0.9  # ~100km east of the default location
    bite_obj.save()

    return bite_obj


@pytest.fixture
def unpublished_object(app_user):
    bite_obj = create_bite_object(user=app_user)
    bite_obj.published_at = None
    bite_obj.save()

    return bite_obj


@pytest.fixture
def soft_deleted_object(app_user):
    bite_obj = create_bite_object(user=app_user)
    bite_obj.soft_delete()

    return bite_obj
