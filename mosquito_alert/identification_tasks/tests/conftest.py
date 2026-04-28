import pytest

from django.contrib.auth import get_user_model
from django.contrib.gis.geos import MultiPolygon, Polygon
from django.utils import timezone

from mosquito_alert.geo.models import EuropeCountry
from mosquito_alert.identification_tasks.models import IdentificationTask
from mosquito_alert.reports.models import Report, Photo
from mosquito_alert.users.models import TigaUser
from mosquito_alert.workspaces.models import WorkspaceMembership

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser")


@pytest.fixture
def tiga_user(db):
    return TigaUser.objects.create()


@pytest.fixture
def country(db):
    return EuropeCountry.objects.create(
        name_engl="test",
        iso3_code="123",
        fid="12",
        geom=MultiPolygon(Polygon.from_bbox((0, 0, 1, 1))),
    )


@pytest.fixture
def _report(tiga_user, country):
    created_at = timezone.now()
    point = country.geom.point_on_surface

    return Report(
        user=tiga_user,
        phone_upload_time=created_at,
        creation_time=created_at,
        current_location_lon=point.x,
        current_location_lat=point.y,
        location_choice=Report.LOCATION_CURRENT,
    )


@pytest.fixture
def _adult_report(_report):
    _report.type = Report.TYPE_ADULT
    return _report


@pytest.fixture
def adult_report(_adult_report):
    _adult_report.save()
    return _adult_report


@pytest.fixture
def identification_task(adult_report):
    _ = Photo.objects.create(report=adult_report, photo="./testdata/splash.png")
    return IdentificationTask.objects.get(report=adult_report)


@pytest.fixture
def user_national_supervisor(user, country):
    WorkspaceMembership.objects.create(
        workspace__country=country, user=user, role=WorkspaceMembership.Role.SUPERVISOR
    )

    return user
