import pytest

from mosquito_alert.geo.tests.factories import EuropeCountryFactory
from mosquito_alert.workspaces.models import Workspace


@pytest.mark.django_db
def test_workspace_created_on_new_country():
    country = EuropeCountryFactory()
    workspace = Workspace.objects.get(country=country)
    assert workspace is not None
