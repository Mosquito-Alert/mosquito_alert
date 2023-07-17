import factory
import factory.fuzzy

from mosquito_alert.breeding_sites.tests.factories import BreedingSiteFactory
from mosquito_alert.geo.tests.factories import GeoLocatedModelFactory
from mosquito_alert.individuals.tests.factories import IndividualFactory
from mosquito_alert.users.tests.factories import UserFactory

from ..models import BiteReport, BreedingSiteReport, IndividualReport, Report


class ReportFactory(GeoLocatedModelFactory):
    user = factory.SubFactory(UserFactory)

    notes = factory.Faker("paragraph")

    @factory.post_generation
    def photos(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of photos were passed in, use them
            for photo in extracted:
                self.photos.add(photo)

    class Meta:
        model = Report


class BiteReportFactory(ReportFactory):
    @factory.post_generation
    def bites(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of bites were passed in, use them
            for photo in extracted:
                self.bites.add(photo)

    class Meta:
        model = BiteReport


class BreedingSiteReportFactory(ReportFactory):
    breeding_site = factory.SubFactory(BreedingSiteFactory)

    has_water = False

    class Meta:
        model = BreedingSiteReport


class IndividualReportFactory(ReportFactory):
    individual = factory.SubFactory(IndividualFactory)

    # taxon = factory.SubFactory(TaxonFactory)

    class Meta:
        model = IndividualReport
