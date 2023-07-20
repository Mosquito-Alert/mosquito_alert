import pytest
import tablib
from django.contrib.gis.gdal.geometries import OGRGeometry
from django.contrib.gis.geos.geometry import GEOSGeometry
from import_export import widgets

from ...import_export.resources import BoundaryResource
from ...import_export.widgets import GeoWidget
from ...models import Boundary, BoundaryGeometry, BoundaryLayer


class TestResource:
    @pytest.fixture
    def boundary_resource(self):
        return BoundaryResource()

    def test_fields(self, boundary_resource):
        fields = boundary_resource.fields

        assert "id" in fields
        assert "code" in fields
        assert "name" in fields
        # assert 'name_ca' in fields
        # assert 'name_es' in fields
        # assert 'name_es' in fields
        assert "parent" in fields

    def test_fields_foreign_key(self, boundary_resource):
        fields = boundary_resource.fields

        assert "boundary_layer" in fields
        widget = fields["boundary_layer"].widget
        assert isinstance(widget, widgets.ForeignKeyWidget)
        assert widget.model == BoundaryLayer

    def test_fields_geometry(self, boundary_resource):
        fields = boundary_resource.fields

        assert "geometry" in fields
        widget = fields["geometry"].widget
        assert isinstance(widget, GeoWidget)
        assert widget.model_field == BoundaryGeometry._meta.get_field("geometry")

    def test_init_instance(self, boundary_resource):
        instance = boundary_resource.init_instance()
        assert isinstance(instance, Boundary)

    def test_import_data(self, boundary_resource, country_bl):
        dataset = tablib.Dataset(
            headers=[
                "GID_0",  # map to code
                "NAME_LTM",  # map to name
                "geometry",
            ]
        )
        dataset.append(
            [
                "ES",
                "Spain",
                OGRGeometry("MULTIPOLYGON (((0 0,0 10,10 10,10 0,0 0)))", srs=4326),
            ]
        )

        kwargs = dict(
            boundary_layer=country_bl,
            name_fieldname="NAME_LTM",
            code_fieldname="GID_0",
        )

        assert Boundary.objects.count() == 0
        assert BoundaryGeometry.objects.count() == 0

        result = boundary_resource.import_data(dataset, raise_errors=True, **kwargs)

        assert not result.has_errors()
        assert len(result.rows) == 1

        assert Boundary.objects.count() == 1
        assert BoundaryGeometry.objects.count() == 1
        instance = Boundary.objects.first()

        assert instance.boundary_layer == country_bl
        assert instance.code == "ES"
        assert instance.name == "Spain"
        assert instance.geometry == GEOSGeometry("MULTIPOLYGON (((0 0, 0 10, 10 10, 10 0, 0 0)))", srid=4326)
