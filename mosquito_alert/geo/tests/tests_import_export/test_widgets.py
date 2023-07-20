from contextlib import nullcontext as does_not_raise

import pytest
from django.contrib.gis.db.models.fields import MultiPointField, MultiPolygonField, PointField, PolygonField
from django.contrib.gis.gdal.error import GDALException
from django.contrib.gis.gdal.geometries import OGRGeometry
from django.contrib.gis.geos.geometry import GEOSGeometry

from ...import_export.widgets import GeoWidget


class TestGeoWidget:
    @pytest.mark.parametrize(
        "model_field, value, expected_result, exception",
        [
            (  # db field is single poly, geom is single and same srid
                PolygonField(srid=4326),
                OGRGeometry("POLYGON ((0 0,0 10,10 10,10 0,0 0))", srs=4326),
                GEOSGeometry("POLYGON ((0 0,0 10,10 10,10 0,0 0))", srid=4326),
                does_not_raise(),
            ),
            (  # db field is multi poly, geom is single and same srid.
                # Expect only to convert to MultiPolygon
                MultiPolygonField(srid=4326),
                OGRGeometry("POLYGON ((0 0,0 10,10 10,10 0,0 0))", srs=4326),
                GEOSGeometry("MULTIPOLYGON (((0 0,0 10,10 10,10 0,0 0)))", srid=4326),
                does_not_raise(),
            ),
            (  # db field is single poly, geom is multiple. Should raise
                PolygonField(srid=4326),
                OGRGeometry("MULTIPOLYGON (((0 0,0 10,10 10,10 0,0 0)))", srs=4326),
                None,
                pytest.raises(GDALException),
            ),
            (  # db field is single point, geom is multiple.  Should raise
                PointField(srid=4326),
                OGRGeometry("MULTIPOINT (0 0)", srs=4326),
                None,
                pytest.raises(GDALException),
            ),
            (  # db field is single point, geom is multiple. diff srid.  Should raise
                PointField(srid=4326),
                OGRGeometry("MULTIPOINT (0 0)", srs=3857),
                None,
                pytest.raises(GDALException),
            ),
            (  # Example of transformation: point in Dallas, from ESPG:3857 to ESPG:4326
                # See: https://epsg.io/transform#s_srs=4326&t_srs=3857&x=-96.8153850&y=32.7672330
                PointField(srid=4326),
                OGRGeometry("POINT (-10777439.359154737 3864448.6366241463)", srs=3857),
                GEOSGeometry("POINT (-96.815385 32.767233)", srid=4326),
                does_not_raise(),
            ),
            (  # Example of transformation: point in Dallas, from ESPG:3857 to ESPG:4326
                # Testing multipoint projection
                # See: https://epsg.io/transform#s_srs=4326&t_srs=3857&x=-96.8153850&y=32.7672330
                MultiPointField(srid=4326),
                OGRGeometry("POINT (-10777439.359154737 3864448.6366241463)", srs=3857),
                GEOSGeometry("MULTIPOINT (-96.815385 32.767233)", srid=4326),
                does_not_raise(),
            ),
        ],
    )
    def test_clean(self, model_field, value, expected_result, exception):
        gw = GeoWidget(model_field=model_field)

        with exception:
            assert gw.clean(value=value) == expected_result

    @pytest.mark.parametrize(
        "value, expected_result",
        [
            (
                GEOSGeometry("POLYGON ((0 0,0 10,10 10,10 0,0 0))", srid=4326),
                "SRID=4326;POLYGON ((0 0, 0 10, 10 10, 10 0, 0 0))",
            ),
            (
                GEOSGeometry("POINT (0 0)", srid=4326),
                "SRID=4326;POINT (0 0)",
            ),
            (
                GEOSGeometry("POINT (0 0)"),
                "POINT (0 0)",
            ),
        ],
    )
    def test_render(self, value, expected_result):
        gw = GeoWidget(model_field=None)

        assert gw.render(value=value) == expected_result
