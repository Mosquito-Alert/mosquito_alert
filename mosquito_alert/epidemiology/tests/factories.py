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

    @classmethod
    def _after_postgeneration(cls, instance, create, results=None):
        # diseases is already set. Do not call obj.save againg
        if results:
            _ = results.pop("diseases", None)
        super()._after_postgeneration(instance=instance, create=create, results=results)

    class Meta:
        model = DiseaseVector
