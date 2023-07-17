import factory
from factory.django import DjangoModelFactory

from ..models import Individual


class IndividualFactory(DjangoModelFactory):
    # taxon = factory.SubFactory(TaxonFactory)

    @factory.post_generation
    def photos(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            for photo in extracted:
                self.photos.add(photo)

    class Meta:
        model = Individual
