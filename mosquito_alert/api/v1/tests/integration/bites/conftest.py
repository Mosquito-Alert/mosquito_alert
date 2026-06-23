from datetime import timedelta
import pytest

from mosquito_alert.reports.models import Report
from mosquito_alert.reports.tests.factories import BiteReportFactory


# NOTE: needed for token with perms fixture
@pytest.fixture
def model_class():
    return Report


@pytest.fixture()
def object(app_user):
    return BiteReportFactory(user=app_user)


@pytest.fixture
def published_object(app_user):
    bite_obj = BiteReportFactory(user=app_user)
    bite_obj.published_at = bite_obj.server_upload_time
    bite_obj.save()
    return bite_obj


@pytest.fixture
def published_object_30_days_ago(app_user, published_object):
    bite_obj = BiteReportFactory(
        user=app_user, creation_time=published_object.creation_time - timedelta(days=30)
    )
    bite_obj.published_at = bite_obj.server_upload_time
    bite_obj.save()
    return bite_obj


@pytest.fixture
def published_object_in_10km(app_user, published_object):
    p = published_object.point.clone()
    p.transform(3857)  # transform to meters
    p.x += 10_000  # ~10km east of the default location
    p.transform(4326)  # transform back to lat/lon

    bite_obj = BiteReportFactory(user=app_user, point=p)
    bite_obj.published_at = bite_obj.server_upload_time
    bite_obj.save()

    return bite_obj


@pytest.fixture
def published_object_in_100km(app_user, published_object):
    p = published_object.point.clone()
    p.transform(3857)  # transform to meters
    p.x += 100_000  # ~100km east of the default location
    p.transform(4326)  # transform back to lat/lon

    bite_obj = BiteReportFactory(user=app_user, point=p)
    bite_obj.published_at = bite_obj.server_upload_time
    bite_obj.save()

    return bite_obj


@pytest.fixture
def unpublished_object(app_user):
    bite_obj = BiteReportFactory(user=app_user)
    bite_obj.published_at = None
    bite_obj.save()
    return bite_obj


@pytest.fixture
def soft_deleted_object(app_user):
    bite_obj = BiteReportFactory(user=app_user)
    bite_obj.soft_delete()

    return bite_obj
