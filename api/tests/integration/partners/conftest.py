import pytest

from django.contrib.gis.geos import Point

from tigaserver_app.models import OrganizationPin


@pytest.fixture
def partner():
    return OrganizationPin.objects.create(
        point=Point(x=0, y=0, srid=4326),
        textual_description="test description",
        page_url="http://www.testurl.com",
    )
