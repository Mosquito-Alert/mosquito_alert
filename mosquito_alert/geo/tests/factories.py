import factory
from factory.django import DjangoModelFactory
from faker import Faker

from ..models import EuropeCountry, NutsEurope

from .fuzzy import FuzzyMultiPolygon, FuzzyGriddedPolygon

fake = Faker()


class EuropeCountryFactory(DjangoModelFactory):
    fid = factory.Sequence(lambda n: "%s" % n)
    cntr_id = factory.Sequence(lambda n: "%s" % n)
    name_engl = factory.LazyAttribute(
        lambda _: fake.country()[
            : EuropeCountry._meta.get_field("name_engl").max_length
        ]
    )
    iso3_code = factory.Sequence(lambda n: "%s" % n)
    geom = FuzzyMultiPolygon(srid=4326, polygon_klass=FuzzyGriddedPolygon)

    class Meta:
        model = EuropeCountry


class NutsEuropeFactory(DjangoModelFactory):
    fid = factory.Sequence(lambda n: "%s" % n)
    nuts_id = factory.Sequence(lambda n: "%s" % n)
    levl_code = 1
    cntr_code = factory.Sequence(lambda n: "%s" % n)
    name_latn = factory.Faker("province", locale="en_CA")
    nuts_name = factory.Faker("province", locale="en_CA")
    geom = FuzzyMultiPolygon(srid=4326, polygon_klass=FuzzyGriddedPolygon)
    europecountry = factory.SubFactory(EuropeCountryFactory)

    class Meta:
        model = NutsEurope
