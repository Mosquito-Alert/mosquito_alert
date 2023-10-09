import pytest
from django.contrib.gis.geos import MultiPolygon, Point, Polygon
from django.db.models.deletion import ProtectedError
from django.db.utils import IntegrityError

from mosquito_alert.utils.tests.test_models import BaseTestTimeStampedModel

from ..models import Boundary, BoundaryGeometry, BoundaryLayer, Location
from .factories import BoundaryFactory, BoundaryGeometryFactory, BoundaryLayerFactory, LocationFactory
from .fuzzy import FuzzyMultiPolygon, FuzzyPoint, FuzzyPolygon
from .models import DummyGeoLocatedModel


@pytest.mark.django_db
class TestBoundaryLayerModel:
    def test_boundary_can_be_null(self):
        BoundaryLayerFactory(boundary=None)

    def test_boundary_type_can_not_be_null(self):
        with pytest.raises(IntegrityError, match=r"not-null constraint"):
            BoundaryLayerFactory(boundary_type=None)

    def test_name_can_not_be_null(self):
        with pytest.raises(IntegrityError, match=r"not-null constraint"):
            BoundaryLayerFactory(name=None)

    @pytest.mark.parametrize("fieldname", ["boundary_type", "level"])
    def test_indexed_fields(self, fieldname):
        assert BoundaryLayer._meta.get_field(fieldname).db_index

    def test_description_can_be_null(self):
        BoundaryLayerFactory(description=None)

    def test_protect_on_bounadary_delete(self):
        bl = BoundaryLayerFactory(boundary=None)
        boundary = BoundaryFactory(boundary_layer=bl)
        bl.boundary = boundary
        bl.save()

        with pytest.raises(ProtectedError):
            boundary.delete()

    def test_trees_must_have_same_boundary_type(self):
        adm_root_node = BoundaryLayerFactory(
            boundary=None, boundary_type=BoundaryLayer.BoundaryType.ADMINISTRATIVE.value
        )

        with pytest.raises(ValueError):
            _ = BoundaryLayerFactory(
                boundary_type=BoundaryLayer.BoundaryType.STATISTICAL.value,
                parent=adm_root_node,
            )

    def test_auto_level_from_parent(self, country_bl):
        bl = BoundaryLayerFactory(level=None, parent=country_bl, boundary_type=country_bl.boundary_type)

        assert bl.level == country_bl.level + 1

    def test_auto_level_to_0_if_root(self):
        bl = BoundaryLayerFactory(level=None, parent=None)

        assert bl.level == 0

    def test_raise_on_level_update_lower_than_parent(self, country_bl):
        bl = BoundaryLayerFactory(level=None, parent=country_bl, boundary_type=country_bl.boundary_type)
        bl.level = 0

        with pytest.raises(ValueError):
            bl.save()

    def test_boundary_owner_is_inherited_from_parent(self):
        bl = BoundaryLayerFactory(boundary=None)
        boundary = BoundaryFactory(boundary_layer=bl)
        bl.boundary = boundary
        bl.save()

        child_bl = BoundaryLayerFactory(boundary=None, parent=bl, boundary_type=bl.boundary_type)

        assert child_bl.boundary == boundary

    def test_update_descendants_boundaries_on_update(self):
        bl = BoundaryLayerFactory(boundary=None)
        boundary = BoundaryFactory(boundary_layer=bl, code="code1")
        bl.boundary = boundary
        bl.save()

        child_bl = BoundaryLayerFactory(parent=bl, boundary_type=bl.boundary_type)

        new_boundary = BoundaryFactory(boundary_layer=bl, code="code2")

        bl.boundary = new_boundary
        bl.save()

        child_bl.refresh_from_db()

        assert child_bl.boundary == new_boundary

    def test_unique_type_level_by_boundary(self):
        b = BoundaryFactory()
        with pytest.raises(IntegrityError, match=r"unique constraint"):
            _ = BoundaryLayerFactory.create_batch(
                size=2,
                boundary=b,
                boundary_type=BoundaryLayer.BoundaryType.ADMINISTRATIVE.value,
                level=0,
            )

        # Same with bounary null
        with pytest.raises(IntegrityError, match=r"unique constraint"):
            _ = BoundaryLayerFactory.create_batch(
                size=2,
                boundary=None,
                boundary_type=BoundaryLayer.BoundaryType.ADMINISTRATIVE.value,
                level=0,
            )

    def test__str__(self):
        bl = BoundaryLayerFactory(
            boundary_type=BoundaryLayer.BoundaryType.ADMINISTRATIVE.value,
            name="test",
        )
        expected_str = "{}{}: {}".format(BoundaryLayer.BoundaryType.ADMINISTRATIVE.value, 0, "test")
        assert bl.__str__() == expected_str


@pytest.mark.django_db
class TestBoundaryModel(BaseTestTimeStampedModel):
    model = Boundary
    factory_cls = BoundaryFactory

    def test_boundary_layer_cannot_be_null(self):
        with pytest.raises(IntegrityError, match=r"not-null constraint"):
            BoundaryFactory(boundary_layer=None)

    def test_cascade_boundary_layer_deletion(self):
        b = BoundaryFactory()
        b.boundary_layer.delete()
        assert Boundary.objects.all().count() == 0

    def test_code_cannot_be_null(self):
        with pytest.raises(IntegrityError, match=r"not-null constraint"):
            _ = BoundaryFactory(code=None)

    @pytest.mark.parametrize("fieldname", ["code", "name"])
    def test_indexed_fields(self, fieldname):
        assert Boundary._meta.get_field(fieldname).db_index

    # def test_name_cannot_be_null(self):
    #    # NOTE: modeltranslation does not deal with nullable values
    #    with pytest.raises(IntegrityError, match=r"not-null constraint"):
    #        _ = BoundaryFactory(name=None)

    def test_boundary_type_property(self):
        b = BoundaryFactory()
        assert b.boundary_type == b.boundary_layer.boundary_type

    def test_geometry_property_return_None_if_no_boundarygeometry(self, country_bl):
        b = BoundaryFactory(boundary_layer=country_bl)

        assert b.geometry is None

    def test_geometry_property_return_geometry(self, country_bl):
        b = BoundaryFactory(boundary_layer=country_bl)
        b_geom = BoundaryGeometryFactory(boundary=b)

        assert b_geom.geometry == b.geometry

    def test_get_geometry_method_returns_geometry(self, country_bl):
        b = BoundaryFactory(boundary_layer=country_bl)
        b_geom = BoundaryGeometryFactory(boundary=b)

        assert b_geom.geometry.equals_exact(b.get_geometry())

    def test_get_geometry_method_return_None_if_no_boudnarygeometry(self, country_bl):
        b = BoundaryFactory(boundary_layer=country_bl)

        assert b.get_geometry() is None

    def test_geometry_property_is_cached(self, country_bl, django_assert_num_queries):
        b = BoundaryFactory(boundary_layer=country_bl)
        _ = BoundaryGeometryFactory(boundary=b)

        with django_assert_num_queries(1):
            _ = b.geometry

        # Now should be cached
        with django_assert_num_queries(0):
            _ = b.geometry

    def test_update_geometry(self):
        b = BoundaryFactory()
        b_geom = BoundaryGeometryFactory(boundary=b)

        b_new_geom = FuzzyMultiPolygon(srid=4326).fuzz()

        b.geometry = b_new_geom
        b.save()

        assert b_geom.geometry.equals_exact(b_new_geom)

    def test_update_geometry_to_None(self):
        b = BoundaryFactory()
        _ = BoundaryGeometryFactory(boundary=b)

        b.geometry = None
        b.save()

        assert BoundaryGeometry.objects.filter(boundary=b).count() == 0

    def test_update_geometry_from_None(self):
        b = BoundaryFactory()

        mpoly = FuzzyMultiPolygon().fuzz()
        b.geometry = mpoly
        b.save()

        assert BoundaryGeometry.objects.get(boundary=b).geometry.equals_exact(mpoly)

    def test_unique_boundarylayer_code(self, country_bl):
        with pytest.raises(IntegrityError, match=r"unique constraint"):
            BoundaryFactory.create_batch(size=2, code="ES", boundary_layer=country_bl)

    def test__str__(self):
        b = BoundaryFactory(name="Random boundary", code="RND")
        expected_output = "Random boundary (RND)"
        assert b.__str__() == expected_output


@pytest.mark.django_db
class TestBoundaryGeometryModel(BaseTestTimeStampedModel):
    model = BoundaryGeometry
    factory_cls = BoundaryGeometryFactory

    def test_boundary_is_primary_key(self, country_bl):
        b = BoundaryFactory(boundary_layer=country_bl)
        b_geom = BoundaryGeometryFactory(boundary=b)

        assert b_geom.pk == b.pk

    def test_cascading_deletion_on_boundary(self, country_bl):
        b = BoundaryFactory(boundary_layer=country_bl)
        _ = BoundaryGeometryFactory(boundary=b)

        b.delete()

        assert BoundaryGeometry.objects.all().count() == 0

    def test_boundary_should_only_have_one_boundarygeometry(self, country_bl):
        b = BoundaryFactory(boundary_layer=country_bl)
        with pytest.raises(IntegrityError, match=r"unique"):
            _ = BoundaryGeometryFactory.create_batch(size=2, boundary=b)

    def test_boundary_related_name(self, country_bl):
        b = BoundaryFactory(boundary_layer=country_bl)
        b_geom = BoundaryGeometryFactory(boundary=b)

        assert b.geometry_model == b_geom

    def test_geometry_srid_is_4326(self):
        assert BoundaryGeometry._meta.get_field("geometry").srid == 4326

    def test_geometry_can_not_be_null(self, country_bl):
        b = BoundaryFactory(boundary_layer=country_bl)
        with pytest.raises(IntegrityError, match=r"not-null constraint"):
            _ = BoundaryGeometryFactory(boundary=b, geometry=None)

    def test_geometry_can_not_be_empty(self, country_bl):
        b = BoundaryFactory(boundary_layer=country_bl)
        # Creating an empty Polygon
        mp = MultiPolygon(Polygon(), srid=4326)

        with pytest.raises(ValueError, match=r"empty"):
            _ = BoundaryGeometryFactory(boundary=b, geometry=mp)

    def test_geometry_field_accepts_polygon(self, country_bl):
        # Check that Polygon is auto-converted to Multipolygon
        b = BoundaryFactory(boundary_layer=country_bl)

        polygon = FuzzyPolygon().fuzz()

        b_geom = BoundaryGeometryFactory(boundary=b, geometry=polygon)
        mpoly = MultiPolygon(polygon)

        assert b_geom.geometry.equals_exact(mpoly)

    def test_geometry_field_raise_setting_polygon_on_geometry_update(self, country_bl):
        # Check that Polygon is auto-converted to Multipolygon on geometry property update
        b = BoundaryFactory(boundary_layer=country_bl)
        b_geom = BoundaryGeometryFactory(boundary=b)

        polygon = FuzzyPolygon().fuzz()
        with pytest.raises(TypeError):
            b_geom.geometry = polygon
            b_geom.save()

    def test_update_linked_locations_on_create(self, country_bl):
        bbox_poly_a = (0, 0, 10, 10)  # x0, y0, x1, y1
        point_in_a = (5, 5)
        point_outside_a = (100, 100)

        location_in_a = LocationFactory(point=Point(point_in_a, srid=4326))
        location_outside_a = LocationFactory(point=Point(point_outside_a, srid=4326))

        boundary_a = BoundaryFactory(boundary_layer=country_bl)
        _ = BoundaryGeometryFactory(
            boundary=boundary_a,
            geometry=MultiPolygon(Polygon.from_bbox(bbox=bbox_poly_a), srid=4326),
        )

        assert list(location_in_a.boundaries.all()) == [boundary_a]
        assert list(location_outside_a.boundaries.all()) == []

    def test_update_linked_locations_on_geometry_update(self, country_bl):
        bbox_poly_a = (0, 0, 10, 10)  # x0, y0, x1, y1
        point_in_a = (5, 5)

        bbox_poly_b = (100, 100, 110, 110)  # x0, y0, x1, y1
        point_in_b = (100, 100)

        location_in_a = LocationFactory(point=Point(point_in_a, srid=4326))
        location_in_b = LocationFactory(point=Point(point_in_b, srid=4326))

        boundary_a = BoundaryFactory(boundary_layer=country_bl)
        ba_geom = BoundaryGeometryFactory(
            boundary=boundary_a,
            geometry=MultiPolygon(Polygon.from_bbox(bbox=bbox_poly_a), srid=4326),
        )

        ba_geom.geometry = MultiPolygon(Polygon.from_bbox(bbox=bbox_poly_b), srid=4326)
        ba_geom.save()

        assert list(location_in_a.boundaries.all()) == []
        assert list(location_in_b.boundaries.all()) == [boundary_a]


@pytest.mark.django_db
class TestLocationModel:
    def test_point_srid_is_4326(self):
        assert Location._meta.get_field("point").srid == 4326

    def test_point_can_not_be_null(self):
        with pytest.raises(IntegrityError, match=r"not-null constraint"):
            LocationFactory(point=None)

    def test_location_type_can_be_null(self):
        LocationFactory(location_type=None)

    def test_boundaries_related_name(self):
        b = BoundaryFactory()

        loc1 = LocationFactory(boundaries=[b])
        loc2 = LocationFactory(boundaries=[b])

        assert frozenset(list(b.locations.all())) == frozenset([loc1, loc2])

    def test_update_boundaries_on_create(self, country_bl):
        bbox_poly_a = (0, 0, 10, 10)  # x0, y0, x1, y1
        point_in_a = (5, 5)
        # Disjoint
        bbox_poly_b = (100, 100, 110, 110)  # x0, y0, x1, y1
        boundary_a = BoundaryFactory(boundary_layer=country_bl)
        _ = BoundaryGeometryFactory(
            boundary=boundary_a,
            geometry=MultiPolygon(Polygon.from_bbox(bbox=bbox_poly_a), srid=4326),
        )

        boundary_b = BoundaryFactory(boundary_layer=country_bl)
        _ = BoundaryGeometryFactory(
            boundary=boundary_b,
            geometry=MultiPolygon(Polygon.from_bbox(bbox=bbox_poly_b), srid=4326),
        )

        location_in_a = LocationFactory(point=Point(point_in_a, srid=4326))

        assert list(location_in_a.boundaries.all()) == [boundary_a]

    def test_update_boundaries_on_point_update(self, country_bl):
        bbox_poly_a = (0, 0, 10, 10)  # x0, y0, x1, y1
        point_in_a = (5, 5)
        # Disjoint
        bbox_poly_b = (100, 100, 110, 110)  # x0, y0, x1, y1
        point_in_b = (105, 105)

        boundary_a = BoundaryFactory(boundary_layer=country_bl)
        _ = BoundaryGeometryFactory(
            boundary=boundary_a,
            geometry=MultiPolygon(Polygon.from_bbox(bbox=bbox_poly_a), srid=4326),
        )

        boundary_b = BoundaryFactory(boundary_layer=country_bl)
        _ = BoundaryGeometryFactory(
            boundary=boundary_b,
            geometry=MultiPolygon(Polygon.from_bbox(bbox=bbox_poly_b), srid=4326),
        )

        location_in_a = LocationFactory(point=Point(point_in_a, srid=4326))

        # Change to point in b
        location_in_a.point = Point(point_in_b, srid=4326)
        location_in_a.save()

        assert list(location_in_a.boundaries.all()) == [boundary_b]

    def test__str__with_location_type(self):
        point = FuzzyPoint(srid=4326).fuzz()
        loc = LocationFactory(point=point)

        expected_output = f"{point.coords} ({loc.location_type})"
        assert loc.__str__() == expected_output

    def test__str__without_location_type(self):
        point = FuzzyPoint(srid=4326).fuzz()
        loc = LocationFactory(point=point, location_type=None)

        expected_output = f"{point.coords}"
        assert loc.__str__() == expected_output


@pytest.mark.django_db
class TestGeoLocatedModel:
    def test_null_location_should_raise(self):
        with pytest.raises(IntegrityError, match=r"not-null constraint"):
            _ = DummyGeoLocatedModel.objects.create(location=None)

    def test_protect_deletion_from_location(self):
        loc = LocationFactory()
        _ = DummyGeoLocatedModel.objects.create(location=loc)

        with pytest.raises(ProtectedError):
            loc.delete()

    def test_location_is_deleted_on_self_delete(self):
        loc = LocationFactory()
        geo_loc = DummyGeoLocatedModel.objects.create(location=loc)

        assert Location.objects.all().count() == 1

        geo_loc.delete()
        assert Location.objects.all().count() == 0
