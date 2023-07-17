import factory
from factory.django import DjangoModelFactory

from mosquito_alert.taxa.models import Taxon
from mosquito_alert.taxa.tests.factories import TaxonFactory

from ..models import Disease, DiseaseVector


class DiseaseFactory(DjangoModelFactory):
    name = factory.Faker("name")

    class Meta:
        model = Disease


class DiseaseVectorFactory(DjangoModelFactory):
    taxon = factory.SubFactory(TaxonFactory, rank=Taxon.TaxonomicRank.SPECIES)

    @factory.post_generation
    def diseases(self, create, extracted, **kwargs):
        if not create or not extracted:
            # Simple build, do nothing
            return

        self.diseases.add(*extracted)

    class Meta:
        model = DiseaseVector
