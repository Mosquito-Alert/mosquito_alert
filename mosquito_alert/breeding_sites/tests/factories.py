import factory

from mosquito_alert.geo.tests.factories import GeoLocatedModelFactory

from ..models import BreedingSite


class BreedingSiteFactory(GeoLocatedModelFactory):
    type = factory.Faker(
        "random_element", elements=BreedingSite.BreedingSiteTypes.values
    )

    class Meta:
        model = BreedingSite
