from abc import ABC
from unittest.mock import patch

import pytest
from django.contrib.gis.geos import MultiPolygon, Point, Polygon
from django.core.exceptions import ValidationError
from django.db import models
from django.db.utils import IntegrityError

from mosquito_alert.utils.tests.test_models import AbstractDjangoModelTestMixin, BaseTestTimeStampedModel

from ..models import Boundary, BoundaryGeometry, BoundaryLayer, Location
from .factories import (
    BoundaryFactory,
    BoundaryGeometryFactory,
    BoundaryLayerFactory,
    DummyGeoLocatedModelFactory,
    LocationFactory,
)
from .fuzzy import FuzzyMultiPolygon, FuzzyPoint, FuzzyPolygon
from .models import DummyGeoLocatedModel


@pytest.mark.django_db
class TestBoundaryLayerModel(AbstractDjangoModelTestMixin):
    model = BoundaryLayer
    factory_cls = BoundaryLayerFactory

    # fields
    def test_boundary_can_be_null(self):
        assert self.model._meta.get_field("boundary").null

    def test_boundary_can_be_blank(self):
        assert self.model._meta.get_field("boundary").blank

    def test_boundary_on_delete_is_protected(self):
        _on_delete = self.model._meta.get_field("boundary").remote_field.on_delete
        assert _on_delete == models.PROTECT

    def test_boundary_related_name(self):
        assert self.model._meta.get_field("boundary").remote_field.related_name == "boundary_layers"

    def test_boundary_type_can_not_be_null(self):
        assert not self.model._meta.get_field("boundary_type").null

    def test_boundary_type_is_db_index(self):
        assert self.model._meta.get_field("boundary_type").db_index

    def test_name_can_not_be_null(self):
        assert not self.model._meta.get_field("name").null

    def test_name_max_length_is_64(self):
        assert self.model._meta.get_field("name").max_length == 64

    def test_level_can_not_be_null(self):
        assert not self.model._meta.get_field("level").null

    def test_level_can_be_blank(self):
        assert self.model._meta.get_field("level").blank

    def test_level_is_db_index(self):
        assert self.model._meta.get_field("level").db_index

    def test_description_can_be_null(self):
        assert self.model._meta.get_field("description").null

    def test_description_can_be_blank(self):
        assert self.model._meta.get_field("description").blank

    # properties
    def test_node_order_by_name(self):
        assert self.model.node_order_by == ["name"]

    # methods
    def test_children_layers_must_have_same_boundary_type_than_parents(self):
        adm_root_node = self.factory_cls(boundary=None, boundary_type=BoundaryLayer.BoundaryType.ADMINISTRATIVE.value)

        with pytest.raises(ValidationError):
            _ = self.factory_cls(
                boundary_type=BoundaryLayer.BoundaryType.STATISTICAL.value,
                parent=adm_root_node,
            )

    def test_level_is_inferred_from_parent_if_not_set(self, country_bl):
        bl = self.factory_cls(level=None, parent=country_bl, boundary_type=country_bl.boundary_type)

        assert bl.level == country_bl.level + 1

    def test_auto_level_to_0_if_root(self):
        bl = self.factory_cls(level=None, parent=None)

        assert bl.level == 0

    def test_raise_on_level_update_lower_than_parent(self, country_bl):
        bl = self.factory_cls(level=None, parent=country_bl, boundary_type=country_bl.boundary_type)
        bl.level = 0

        with pytest.raises(ValidationError):
            bl.save()

    def test_boundary_owner_is_inherited_from_parent(self):
        bl = self.factory_cls(boundary=None)
        boundary = BoundaryFactory(boundary_layer=bl)
        bl.boundary = boundary
        bl.save()

        child_bl = self.factory_cls(boundary=None, parent=bl, boundary_type=bl.boundary_type)

        assert child_bl.boundary == boundary

    def test_update_descendants_boundaries_on_update(self):
        bl = self.factory_cls(boundary=None)
        boundary = BoundaryFactory(boundary_layer=bl, code="code1")
        bl.boundary = boundary
        bl.save()

        child_bl = self.factory_cls(parent=bl, boundary_type=bl.boundary_type)

        new_boundary = BoundaryFactory(boundary_layer=bl, code="code2")

        bl.boundary = new_boundary
        bl.save()

        child_bl.refresh_from_db()

        assert child_bl.boundary == new_boundary

    # meta
    def test_unique_type_level_by_boundary(self):
        b = BoundaryFactory()
        with pytest.raises(IntegrityError, match=r"unique constraint"):
            _ = self.factory_cls.create_batch(
                size=2,
                boundary=b,
                boundary_type=BoundaryLayer.BoundaryType.ADMINISTRATIVE.value,
                level=0,
            )

        # Same with bounary null
        with pytest.raises(IntegrityError, match=r"unique constraint"):
            _ = self.factory_cls.create_batch(
                size=2,
                boundary=None,
                boundary_type=BoundaryLayer.BoundaryType.ADMINISTRATIVE.value,
                level=0,
            )

    def test__str__(self):
        bl = self.factory_cls(
            boundary_type=BoundaryLayer.BoundaryType.ADMINISTRATIVE.value,
            name="test",
        )
        expected_str = "{}{}: {}".format(BoundaryLayer.BoundaryType.ADMINISTRATIVE.value, 0, "test")
        assert bl.__str__() == expected_str


@pytest.mark.django_db
class TestBoundaryModel(BaseTestTimeStampedModel):
    model = Boundary
    factory_cls = BoundaryFactory

    # fields
    def test_boundary_layer_cannot_be_null(self):
        assert not self.model._meta.get_field("boundary_layer").null

    def test_boundary_layer_on_delete_cascade(self):
        _on_delete = self.model._meta.get_field("boundary_layer").remote_field.on_delete
        assert _on_delete == models.CASCADE

    def test_code_cannot_be_null(self):
        assert not self.model._meta.get_field("code").null

    def test_code_max_length_is_16(self):
        assert self.model._meta.get_field("code").max_length == 16

    def test_code_is_db_index(self):
        assert self.model._meta.get_field("code").db_index

    def test_name_can_not_be_null(self):
        assert not self.model._meta.get_field("name").null

    def test_name_max_length_is_128(self):
        assert self.model._meta.get_field("name").max_length == 128

    def test_name_is_db_index(self):
        assert self.model._meta.get_field("name").db_index

    # custom properties
    def test_node_order_by_name(self):
        assert self.model.node_order_by == ["name"]

    def test_boundary_type_property(self):
        b = self.factory_cls()
        assert b.boundary_type == b.boundary_layer.boundary_type

    def test_geometry_property_returns_same_as_get_geometry(self):
        obj = self.factory_cls()

        with patch.object(obj, "get_geometry", return_value="mocking_test") as mocked_method:
            assert obj.geometry == "mocking_test"

        mocked_method.assert_called_once()

    def test_geometry_property_is_cached(self, country_bl, django_assert_num_queries):
        b = self.factory_cls(boundary_layer=country_bl)
        _ = BoundaryGeometryFactory(boundary=b)

        with django_assert_num_queries(1):
            _ = b.geometry

        # Now should be cached
        with django_assert_num_queries(0):
            _ = b.geometry

    # methods
    def test_get_geometry_method_returns_geometry(self, country_bl):
        b = self.factory_cls(boundary_layer=country_bl)
        b_geom = BoundaryGeometryFactory(boundary=b)

        assert b_geom.geometry.equals_exact(b.get_geometry())

    def test_get_geometry_method_return_None_if_no_boudnarygeometry(self, country_bl):
        b = self.factory_cls(boundary_layer=country_bl)

        assert b.get_geometry() is None

    def test_update_geometry(self):
        b = self.factory_cls()
        b_geom = BoundaryGeometryFactory(boundary=b)

        b_new_geom = FuzzyMultiPolygon(srid=4326).fuzz()

        b.geometry = b_new_geom
        b.save()

        assert b_geom.geometry.equals_exact(b_new_geom)

    def test_update_geometry_to_None(self):
        b = self.factory_cls()
        _ = BoundaryGeometryFactory(boundary=b)

        b.geometry = None
        b.save()

        assert BoundaryGeometry.objects.filter(boundary=b).count() == 0

    def test_update_geometry_from_None(self):
        b = self.factory_cls()

        mpoly = FuzzyMultiPolygon().fuzz()
        b.geometry = mpoly
        b.save()

        assert BoundaryGeometry.objects.get(boundary=b).geometry.equals_exact(mpoly)

    # meta
    def test_unique_boundarylayer_code(self, country_bl):
        with pytest.raises(IntegrityError, match=r"unique constraint"):
            self.factory_cls.create_batch(size=2, code="ES", boundary_layer=country_bl)

    def test__str__(self):
        b = self.factory_cls(name="Random boundary", code="RND")
        expected_output = "Random boundary (RND)"
        assert b.__str__() == expected_output


@pytest.mark.django_db
class TestBoundaryGeometryModel(BaseTestTimeStampedModel):
    model = BoundaryGeometry
    factory_cls = BoundaryGeometryFactory

    # fields
    def test_boundary_fk_is_unique(self):
        assert self.model._meta.get_field("boundary").unique

    def test_boundary_is_pk(self):
        assert self.model._meta.get_field("boundary").primary_key

    def test_boundary_can_not_be_null(self):
        assert not self.model._meta.get_field("boundary").null

    def test_boundary_on_delete_cascade(self):
        _on_delete = self.model._meta.get_field("boundary").remote_field.on_delete
        assert _on_delete == models.CASCADE

    def test_boundary_related_name(self):
        assert self.model._meta.get_field("boundary").remote_field.related_name == "geometry_model"

    def test_geometry_class_is_multipolygon(self):
        assert self.model._meta.get_field("geometry").geom_class == MultiPolygon

    def test_geometry_srid_is_4326(self):
        assert self.model._meta.get_field("geometry").srid == 4326

    def test_geometry_can_not_be_null(self):
        assert not self.model._meta.get_field("geometry").null

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
class TestLocationModel(AbstractDjangoModelTestMixin):
    model = Location
    factory_cls = LocationFactory

    # fields
    def test_boundaries_related_name(self):
        assert self.model._meta.get_field("boundaries").remote_field.related_name == "locations"

    def test_boundaries_can_be_blank(self):
        assert self.model._meta.get_field("boundaries").blank

    def test_point_can_not_be_null(self):
        assert not self.model._meta.get_field("point").null

    def test_point_can_not_be_blank(self):
        assert not self.model._meta.get_field("point").blank

    def test_point_srid_is_4326(self):
        assert self.model._meta.get_field("point").srid == 4326

    def test_location_type_can_be_null(self):
        assert self.model._meta.get_field("location_type").null

    def test_location_type_can_be_blank(self):
        assert self.model._meta.get_field("location_type").blank

    # methods
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

    # meta
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


class BaseTestGeoLocatedModel(AbstractDjangoModelTestMixin, ABC):
    def test_location_fk_is_unique(self):
        assert self.model._meta.get_field("location").unique

    def test_location_can_not_be_null(self):
        assert not self.model._meta.get_field("location").null

    def test_location_on_delete_protect(self):
        _on_delete = self.model._meta.get_field("location").remote_field.on_delete
        assert _on_delete == models.PROTECT

    def test_location_related_name(self):
        assert self.model._meta.get_field("location").remote_field.related_name == "+"

    def test_location_is_deleted_on_self_delete(self):
        loc = LocationFactory()
        geo_loc = self.factory_cls(location=loc)

        assert Location.objects.all().count() == 1

        geo_loc.delete()
        assert Location.objects.all().count() == 0


@pytest.mark.django_db
class TestDummyGeoLocatedModel(BaseTestGeoLocatedModel):
    model = DummyGeoLocatedModel
    factory_cls = DummyGeoLocatedModelFactory
