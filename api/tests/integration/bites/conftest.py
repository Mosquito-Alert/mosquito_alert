import pytest

from tigapublic.models import MapAuxReports
from tigaserver_app.models import Report

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

    _ = MapAuxReports.objects.get_or_create(
        version_uuid=bite_obj,
        defaults={
            "id": 10,
            "user_id": bite_obj.user.pk,
            "ref_system": 4326,
            "type": bite_obj.type,
            "final_expert_status": 1,
            "visible": True,
        },
    )
    return bite_obj

@pytest.fixture
def unpublished_object(app_user):
    bite_obj = create_bite_object(user=app_user)

    _ = MapAuxReports.objects.filter(version_uuid=bite_obj).delete()
    return bite_obj

@pytest.fixture
def soft_deleted_object(app_user):
    bite_obj = create_bite_object(user=app_user)
    bite_obj.soft_delete()

    return bite_obj
