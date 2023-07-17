import factory
from factory.django import DjangoModelFactory

from ..models import Boundary, BoundaryGeometry, BoundaryLayer, Location
from .fuzzy import FuzzyMultiPolygon, FuzzyPoint
from .models import DummyGeoLocatedModel


class BoundaryLayerFactory(DjangoModelFactory):
    boundary = factory.RelatedFactory(
        "mosquito_alert.geo.tests.factories.BoundaryFactory",
        factory_related_name="boundary_layer",
    )
    boundary_type = factory.Faker(
        "random_element", elements=BoundaryLayer.BoundaryType.values
    )
    name = factory.Faker("name")
    level = factory.Faker("random_int", min=0, max=5)
    description = factory.Faker("paragraph")

    class Meta:
        model = BoundaryLayer
        # django_get_or_create = ["boundary_type", "level"]


class BoundaryFactory(DjangoModelFactory):
    boundary_layer = factory.SubFactory(BoundaryLayerFactory)
    code = factory.Sequence(lambda n: "CODE%s" % n)
    created_at = factory.Faker("date_time")
    name = factory.Faker("country")
    updated_at = factory.Faker("date_time")

    class Meta:
        model = Boundary


class BoundaryFactoryWithGeometry(BoundaryFactory):
    geometry_model = factory.RelatedFactory(
        "mosquito_alert.geo.tests.factories.BoundaryGeometryFactory",
        factory_related_name="boundary",
    )

    class Meta:
        model = Boundary


class BoundaryGeometryFactory(DjangoModelFactory):
    boundary = factory.SubFactory(BoundaryFactory, geometry_model=None)

    created_at = factory.Faker("date_time")
    geometry = FuzzyMultiPolygon(srid=4326)
    updated_at = factory.Faker("date_time")

    class Meta:
        model = BoundaryGeometry


class LocationFactory(DjangoModelFactory):
    point = FuzzyPoint(srid=4326)
    location_type = factory.Faker(
        "random_element", elements=Location.LocationType.values
    )

    @factory.post_generation
    def boundaries(self, create, extracted, **kwargs):
        if not create or not extracted:
            # Simple build, do nothing
            return

        self.boundaries.add(*extracted)

    class Meta:
        model = Location


class GeoLocatedModelFactory(DjangoModelFactory):
    location = factory.Maybe(
        decider=factory.LazyAttribute(lambda o: o.point is not None),
        yes_declaration=factory.LazyAttribute(lambda o: LocationFactory(point=o.point)),
        no_declaration=factory.SubFactory(LocationFactory),
    )

    class Meta:
        abstract = True

    class Params:
        point = None


class DummyGeoLocatedModelFactory(GeoLocatedModelFactory):
    class Meta:
        model = DummyGeoLocatedModel
