import factory
from factory.django import DjangoModelFactory
from faker import Faker

from django.contrib.gis.geos import GEOSGeometry, MultiPolygon
from django.db.models.signals import post_save

from shapely import wkt
from shapely.affinity import scale

from ..models import EuropeCountry, NutsEurope

from .fuzzy import FuzzyMultiPolygon, FuzzyGriddedPolygon

fake = Faker()


def scale_geom(geom: GEOSGeometry, factor=0.1):
    if geom is None:
        return None

    # ensure GEOSGeometry
    if not hasattr(geom, "wkt"):
        geom = GEOSGeometry(geom.wkt, srid=geom.srid)

    # convert to Shapely
    shapely_geom = wkt.loads(geom.wkt)

    # scale
    scaled = scale(
        shapely_geom,
        xfact=factor,
        yfact=factor,
        origin="centroid",
    )

    # back to GEOS
    return GEOSGeometry(scaled.wkt, srid=geom.srid)


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


@factory.django.mute_signals(post_save)
class EuropeCountryWithoutSignalFactoryFactory(EuropeCountryFactory):
    class Meta:
        model = EuropeCountry


class NutsEuropeFactory(DjangoModelFactory):
    fid = factory.Sequence(lambda n: "%s" % n)
    nuts_id = factory.Sequence(lambda n: "%s" % n)
    cntr_code = factory.Sequence(lambda n: "%s" % n)
    name_latn = factory.Faker("province", locale="en_CA")
    nuts_name = factory.Faker("province", locale="en_CA")
    europecountry = factory.SubFactory(EuropeCountryFactory)

    geom = factory.LazyAttribute(
        lambda obj: (
            MultiPolygon(
                scale_geom(obj.europecountry.geom[0]), srid=obj.europecountry.geom.srid
            )
            if obj.europecountry and obj.europecountry.geom
            else FuzzyMultiPolygon(srid=4326, polygon_klass=FuzzyGriddedPolygon).fuzz()
        )
    )

    class Meta:
        model = NutsEurope
