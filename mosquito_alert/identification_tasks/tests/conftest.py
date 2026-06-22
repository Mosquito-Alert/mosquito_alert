import pytest

from django.contrib.gis.geos import MultiPolygon, Polygon

from mosquito_alert.geo.tests.factories import CountryFactory
from mosquito_alert.identification_tasks.tests.factories import (
    IdentificationTaskFactory,
)
from mosquito_alert.users.tests.factories import UserFactory
from mosquito_alert.workspaces.models import WorkspaceMembership


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def country(db):
    return CountryFactory(
        geom=MultiPolygon(Polygon.from_bbox((0, 0, 1, 1))),
    )


@pytest.fixture
def identification_task(db, country):
    return IdentificationTaskFactory(report__point=country.geom.point_on_surface)


@pytest.fixture
def user_national_supervisor(user, country):
    WorkspaceMembership.objects.create(
        workspace=country.workspaces.first(),
        user=user,
        role=WorkspaceMembership.Role.SUPERVISOR,
    )

    return user
