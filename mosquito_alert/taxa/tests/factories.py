import random

import factory
from factory.django import DjangoModelFactory
from faker import Faker
from faker_biology.taxonomy import ModelOrganism

from mosquito_alert.geo.tests.factories import BoundaryFactory

from ..models import SpecieDistribution, Taxon

_bio_faker = Faker()
_bio_faker.add_provider(ModelOrganism)


def get_or_create_root_taxon():
    obj, _ = Taxon.objects.get_or_create(
        rank=Taxon.TaxonomicRank.DOMAIN, defaults={"name": "life", "common_name": "life"}
    )

    return obj


class TaxonFactory(DjangoModelFactory):
    class Meta:
        model = Taxon

    common_name = factory.LazyFunction(_bio_faker.organism)

    @factory.sequence
    def name(n):
        max_length = 64  # See Taxon.name.max_length
        fake_name = _bio_faker.organism_latin()
        if len(fake_name) + n > max_length:
            fake_name = fake_name[: max_length - n]
        return fake_name + str(n)

    @factory.lazy_attribute
    def parent(self):
        return get_or_create_root_taxon()

    @factory.lazy_attribute
    def rank(self):
        if self.parent:
            return min(filter(lambda x: x > self.parent.rank, Taxon.TaxonomicRank.values))
        else:
            return random.choice(Taxon.TaxonomicRank.values)


class SpecieDistributionFactory(DjangoModelFactory):
    boundary = factory.SubFactory(BoundaryFactory)
    taxon = factory.SubFactory(TaxonFactory, rank=Taxon.TaxonomicRank.SPECIES)

    source = factory.Faker("random_element", elements=SpecieDistribution.DataSource.values)

    class Meta:
        model = SpecieDistribution
        # django_get_or_create = ("boundary", "taxon", "source")
