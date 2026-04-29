import factory
from factory.django import DjangoModelFactory

from ..models import Workspace


class WorkspaceFactory(DjangoModelFactory):
    class Meta:
        model = Workspace

    # Passing in workspace=None to prevent EuropeCountryFactory from creating another workspace
    # (this disables the RelatedFactory)
    country = factory.SubFactory(
        "mosquito_alert.geo.tests.factories.EuropeCountryWithoutSignalsFactory",
        workspace=None,
    )
