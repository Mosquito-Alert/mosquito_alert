import factory
from factory.django import DjangoModelFactory
from faker import Faker
from faker_biology.taxonomy import ModelOrganism

from mosquito_alert.geo.tests.factories import BoundaryFactory

from ..models import SpecieDistribution, Taxon

_bio_faker = Faker()
_bio_faker.add_provider(ModelOrganism)


class TaxonFactory(DjangoModelFactory):
    rank = factory.Faker("random_element", elements=Taxon.TaxonomicRank.values)
    name = _bio_faker.organism_latin()
    created_at = factory.Faker("date_time")
    common_name = _bio_faker.organism()
    parent = None

    class Meta:
        model = Taxon
        django_get_or_create = ("name", "rank")


class SpecieDistributionFactory(DjangoModelFactory):
    boundary = factory.SubFactory(BoundaryFactory)
    taxon = factory.SubFactory(TaxonFactory, rank=Taxon.TaxonomicRank.SPECIES)

    source = factory.Faker("random_element", elements=SpecieDistribution.DataSource.values)
    status = factory.Faker("random_element", elements=SpecieDistribution.DistributionStatus.values)

    class Meta:
        model = SpecieDistribution
        # django_get_or_create = ("boundary", "taxon", "source")
