import pytest
from django.contrib.gis.geos import MultiPoint, MultiPolygon, Point, Polygon

from ..models import Boundary
from .factories import BoundaryFactory, BoundaryFactoryWithGeometry, DummyGeoLocatedModelFactory, LocationFactory


def create_multipolygon_from_bbox(bbox):
    return MultiPolygon(Polygon.from_bbox(bbox=bbox), srid=4326)


@pytest.fixture()
def small_multipolygon():
    return create_multipolygon_from_bbox(bbox=(0, 0, 10, 10))


@pytest.fixture()
def large_multipolygon():
    return create_multipolygon_from_bbox(bbox=(0, 0, 100, 100))


@pytest.fixture()
def small_boundary(country_bl, small_multipolygon):
    return BoundaryFactoryWithGeometry(boundary_layer=country_bl, geometry_model__geometry=small_multipolygon)


@pytest.fixture()
def large_boundary(country_bl, large_multipolygon):
    return BoundaryFactoryWithGeometry(boundary_layer=country_bl, geometry_model__geometry=large_multipolygon)


@pytest.mark.django_db
class TestBoundaryManager:
    @property
    def objects(self):
        # Adding all() to force queryset level, not manager level.
        return Boundary.objects.all()

    def test_have_boundary_layer_conflicts(self, country_bl):
        _ = BoundaryFactory(boundary_layer=country_bl)

        assert self.objects.have_boundary_layer_conflicts().count() == 0

        b1 = BoundaryFactory(boundary_layer=country_bl)
        b1.depth = country_bl.depth + 1
        b1.save()

        assert list(self.objects.have_boundary_layer_conflicts()) == [b1]

    def test_first_by_area(self, small_boundary, large_boundary):
        assert self.objects.count() == 2

        assert self.objects.first_by_area() == large_boundary

    def test_prefetch_geometry(self):
        qs = self.objects.prefetch_geometry()

        assert "geometry_model" in qs._prefetch_related_lookups

    def test_reverse_geocoding_should_raise_nonpoint_input(self):
        with pytest.raises(ValueError):
            self.objects.reverse_geocoding(point="a")

        with pytest.raises(ValueError):
            self.objects.reverse_geocoding(point=Polygon())

    def test_reverse_geocoding_single_point(self, country_bl):
        a_bbox = (0, 0, 10, 10)  # x0, y0, x1, y1
        b_bbox = (100, 100, 110, 110)  # x0, y0, x1, y1

        point_in_a = Point(5, 5)
        point_in_b = Point(105, 105)
        point_outside = Point(-10, -10)

        boundary_a = BoundaryFactoryWithGeometry(
            boundary_layer=country_bl,
            geometry_model__geometry=MultiPolygon(Polygon.from_bbox(bbox=a_bbox), srid=4326),
        )

        boundary_b = BoundaryFactoryWithGeometry(
            boundary_layer=country_bl,
            geometry_model__geometry=MultiPolygon(Polygon.from_bbox(bbox=b_bbox), srid=4326),
        )

        assert list(self.objects.reverse_geocoding(point=point_in_a)) == [boundary_a]
        assert list(self.objects.reverse_geocoding(point=point_in_b)) == [boundary_b]
        assert list(self.objects.reverse_geocoding(point=point_outside)) == []

    def test_reverse_geocoding_multi_point(self, country_bl):
        a_bbox = (0, 0, 10, 10)  # x0, y0, x1, y1
        b_bbox = (100, 100, 110, 110)  # x0, y0, x1, y1

        point_in_a = Point(5, 5)
        point_in_b = Point(105, 105)
        point_outside = Point(-10, -10)
        multipoint_a_out = MultiPoint(point_outside, point_in_a)
        multipoint_a_b = MultiPoint(point_in_a, point_in_b)
        multipoint_b_out = MultiPoint(point_outside, point_in_b)

        boundary_a = BoundaryFactoryWithGeometry(
            boundary_layer=country_bl,
            geometry_model__geometry=MultiPolygon(Polygon.from_bbox(bbox=a_bbox), srid=4326),
        )

        boundary_b = BoundaryFactoryWithGeometry(
            boundary_layer=country_bl,
            geometry_model__geometry=MultiPolygon(Polygon.from_bbox(bbox=b_bbox), srid=4326),
        )

        assert list(self.objects.reverse_geocoding(point=multipoint_a_out)) == [boundary_a]
        assert frozenset(list(self.objects.reverse_geocoding(point=multipoint_a_b))) == frozenset(
            [
                boundary_b,
                boundary_a,
            ]
        )
        assert list(self.objects.reverse_geocoding(point=multipoint_b_out)) == [boundary_b]

    def test_fuzzy_reverse_polygon_geocoding_should_raise_nonpolygon_input(self):
        with pytest.raises(ValueError):
            self.objects.fuzzy_reverse_polygon_geocoding(polygon="a")

        with pytest.raises(ValueError):
            self.objects.fuzzy_reverse_polygon_geocoding(polygon=Point())

    def test_fuzzy_reverse_polygon_geocoding_single_polygon(self, country_bl):
        a_bbox = (0, 0, 10, 10)  # x0, y0, x1, y1
        b_bbox = (100, 100, 110, 110)  # x0, y0, x1, y1

        polygon_in_a = Polygon.from_bbox(bbox=(4, 4, 6, 6))
        polygon_in_b = Polygon.from_bbox(bbox=(104, 104, 106, 106))
        polygon_outside = Polygon.from_bbox(bbox=(-10, -10, -15, -15))

        boundary_a = BoundaryFactoryWithGeometry(
            boundary_layer=country_bl,
            geometry_model__geometry=MultiPolygon(Polygon.from_bbox(bbox=a_bbox), srid=4326),
        )

        boundary_b = BoundaryFactoryWithGeometry(
            boundary_layer=country_bl,
            geometry_model__geometry=MultiPolygon(Polygon.from_bbox(bbox=b_bbox), srid=4326),
        )

        assert list(self.objects.fuzzy_reverse_polygon_geocoding(polygon=polygon_in_a)) == [boundary_a]
        assert list(self.objects.fuzzy_reverse_polygon_geocoding(polygon=polygon_in_b)) == [boundary_b]
        assert list(self.objects.fuzzy_reverse_polygon_geocoding(polygon=polygon_outside)) == []

    def test_fuzzy_reverse_polygon_geocoding_multi_polygon(self, country_bl):
        a_bbox = (0, 0, 10, 10)  # x0, y0, x1, y1
        b_bbox = (100, 100, 110, 110)  # x0, y0, x1, y1

        polygon_in_a = Polygon.from_bbox(bbox=(4, 4, 6, 6))
        polygon_in_b = Polygon.from_bbox(bbox=(104, 104, 106, 106))
        polygon_outside = Polygon.from_bbox(bbox=(-10, -10, -15, -15))
        multipoly_a_out = MultiPolygon(polygon_outside, polygon_in_a)
        multipoly_a_b = MultiPolygon(polygon_in_a, polygon_in_b)
        multipoly_b_out = MultiPolygon(polygon_outside, polygon_in_b)

        boundary_a = BoundaryFactoryWithGeometry(
            boundary_layer=country_bl,
            geometry_model__geometry=MultiPolygon(Polygon.from_bbox(bbox=a_bbox), srid=4326),
        )

        boundary_b = BoundaryFactoryWithGeometry(
            boundary_layer=country_bl,
            geometry_model__geometry=MultiPolygon(Polygon.from_bbox(bbox=b_bbox), srid=4326),
        )

        assert list(self.objects.fuzzy_reverse_polygon_geocoding(polygon=multipoly_a_out)) == [boundary_a]
        assert frozenset(list(self.objects.fuzzy_reverse_polygon_geocoding(polygon=multipoly_a_b))) == frozenset(
            [
                boundary_b,
                boundary_a,
            ]
        )
        assert list(self.objects.fuzzy_reverse_polygon_geocoding(polygon=multipoly_b_out)) == [boundary_b]


@pytest.mark.django_db
@pytest.mark.parametrize("factory_cls", [LocationFactory, DummyGeoLocatedModelFactory])
class TestLocationManager:
    @pytest.fixture
    def factory_cls(self):
        return LocationFactory

    # NOTE: All factories must allow init the 'point' param.

    def test_filter_by_boundary_without_descendants(self, factory_cls, country_bl):
        a_bbox = (0, 0, 10, 10)  # x0, y0, x1, y1
        a_child_bbox = (1, 1, 5, 5)
        b_bbox = (100, 100, 110, 110)  # x0, y0, x1, y1

        point_inside_a_child = Point(2, 2)

        boundary_a = BoundaryFactoryWithGeometry(
            boundary_layer=country_bl,
            geometry_model__geometry=MultiPolygon(Polygon.from_bbox(bbox=a_bbox), srid=4326),
        )

        boundary_a_child = BoundaryFactoryWithGeometry(
            parent=boundary_a,
            boundary_layer=country_bl,
            geometry_model__geometry=MultiPolygon(Polygon.from_bbox(bbox=a_child_bbox), srid=4326),
        )

        boundary_b = BoundaryFactoryWithGeometry(
            boundary_layer=country_bl,
            geometry_model__geometry=MultiPolygon(Polygon.from_bbox(bbox=b_bbox), srid=4326),
        )

        model_qs = factory_cls._meta.model.objects.all()

        # Creating Location inside a (inside the a child)
        loc_in_a = factory_cls(point=point_inside_a_child)

        boundary_a.refresh_from_db()

        assert list(model_qs.filter_by_boundary(boundaries=boundary_a, include_descendants=False)) == [loc_in_a]

        assert list(model_qs.filter_by_boundary(boundaries=boundary_a_child, include_descendants=False)) == [loc_in_a]

        assert list(model_qs.filter_by_boundary(boundaries=boundary_b, include_descendants=False)) == []

    def test_filter_by_boundary_with_descendants(self, factory_cls, country_bl):
        a_bbox = (0, 0, 10, 10)  # x0, y0, x1, y1
        a_child_bbox = (20, 20, 30, 30)
        b_bbox = (100, 100, 110, 110)  # x0, y0, x1, y1

        point_inside_a_child = Point(21, 21)

        boundary_a = BoundaryFactoryWithGeometry(
            boundary_layer=country_bl,
            geometry_model__geometry=MultiPolygon(Polygon.from_bbox(bbox=a_bbox), srid=4326),
        )

        boundary_a_child = BoundaryFactoryWithGeometry(
            parent=boundary_a,
            boundary_layer=country_bl,
            geometry_model__geometry=MultiPolygon(Polygon.from_bbox(bbox=a_child_bbox), srid=4326),
        )

        boundary_b = BoundaryFactoryWithGeometry(
            boundary_layer=country_bl,
            geometry_model__geometry=MultiPolygon(Polygon.from_bbox(bbox=b_bbox), srid=4326),
        )

        model_qs = factory_cls._meta.model.objects.all()

        # Creating Location inside a (inside the a child)
        loc_in_a_child = factory_cls(point=point_inside_a_child)

        boundary_a.refresh_from_db()

        assert list(model_qs.filter_by_boundary(boundaries=boundary_a, include_descendants=False)) == []

        assert list(model_qs.filter_by_boundary(boundaries=boundary_a_child, include_descendants=False)) == [
            loc_in_a_child
        ]

        assert list(model_qs.filter_by_boundary(boundaries=boundary_a, include_descendants=True)) == [loc_in_a_child]

        assert list(model_qs.filter_by_boundary(boundaries=boundary_a_child, include_descendants=True)) == [
            loc_in_a_child
        ]

        assert list(model_qs.filter_by_boundary(boundaries=boundary_b, include_descendants=True)) == []

    def test_filter_by_polygon_intersection(self, factory_cls):
        a_poly = Polygon.from_bbox(bbox=(0, 0, 10, 10))

        point_in_a = Point(2, 2)
        point_out_a = Point(102, 102)

        loc_in_a = factory_cls(point=point_in_a)
        factory_cls(point=point_out_a)

        model_qs = factory_cls._meta.model.objects.all()

        assert list(model_qs.filter_by_polygon_intersection(polygon=a_poly, negate=False)) == [loc_in_a]

    def test_negate_filter_by_polygon_intersection(self, factory_cls):
        a_poly = Polygon.from_bbox(bbox=(0, 0, 10, 10))

        point_in_a = Point(2, 2)
        point_out_a = Point(102, 102)

        factory_cls(point=point_in_a)
        loc_out_a = factory_cls(point=point_out_a)

        model_qs = factory_cls._meta.model.objects.all()

        assert list(model_qs.filter_by_polygon_intersection(polygon=a_poly, negate=True)) == [loc_out_a]

    def test_first_by_distance(self, factory_cls):
        query_point = Point(0, 0, srid=4326)

        near_point = Point(20, 20, srid=4326)
        far_point = Point(100, 100, srid=4326)

        near_loc = factory_cls(point=near_point)
        factory_cls(point=far_point)

        model_qs = factory_cls._meta.model.objects.all()

        assert model_qs.first_by_distance(point=query_point) == near_loc

    def test_order_by_distance(self, factory_cls):
        query_point = Point(0, 0, srid=4326)

        near_point = Point(20, 20, srid=4326)
        far_point = Point(100, 100, srid=4326)

        near_loc = factory_cls(point=near_point)
        far_loc = factory_cls(point=far_point)

        model_qs = factory_cls._meta.model.objects.all()

        assert list(model_qs.order_by_distance(point=query_point)) == [
            near_loc,
            far_loc,
        ]

    def test_within_circle(self, factory_cls):
        point_a = Point(0, 0, srid=4326)
        point_b = Point(1, 1, srid=4326)
        point_a_b_mid = Point(0.5, 0.5, srid=4326)

        point_out = Point(90, 90, srid=4326)

        # Used https://geographiclib.sourceforge.io/cgi-bin/GeodSolve
        # for geodesic distance computation
        distance_between_points = 156899  # in meters

        loc_a = factory_cls(point=point_a)
        loc_b = factory_cls(point=point_b)
        loc_a_b_mid = factory_cls(point=point_a_b_mid)

        model_qs = factory_cls._meta.model.objects.all()

        assert list(model_qs.within_circle(center_point=point_b, radius_meters=distance_between_points / 2)) == [loc_b]

        assert frozenset(
            list(model_qs.within_circle(center_point=point_a_b_mid, radius_meters=distance_between_points))
        ) == frozenset([loc_a, loc_b, loc_a_b_mid])

        assert list(model_qs.within_circle(center_point=point_out, radius_meters=0)) == []
