from django.contrib.gis.gdal import CoordTransform, SpatialReference
from django.contrib.gis.gdal.error import GDALException
from django.contrib.gis.gdal.geometries import OGRGeometry
from django.contrib.gis.gdal.geomtype import OGRGeomType
from django.contrib.gis.geos.geometry import GEOSGeometry
from import_export.widgets import Widget


class GeoWidget(Widget):
    # Acceptable 'base' types for a multi-geometry type.
    MULTI_TYPES = {
        1: OGRGeomType("MultiPoint"),
        2: OGRGeomType("MultiLineString"),
        3: OGRGeomType("MultiPolygon"),
        OGRGeomType("Point25D").num: OGRGeomType("MultiPoint25D"),
        OGRGeomType("LineString25D").num: OGRGeomType("MultiLineString25D"),
        OGRGeomType("Polygon25D").num: OGRGeomType("MultiPolygon25D"),
    }

    def __init__(self, model_field, **kwargs):
        self.model_field = model_field
        super().__init__(**kwargs)

    def clean(self, value, row=None, **kwargs):
        """
        Returns an appropriate GEOS object from the imported value.

        Since DataSource is used for the import of files, the 'value' param
        is a GDAL object.

        GDAL object is transformed into an GEOS object.
        """
        return GEOSGeometry(self._verify_geom(geom=value))

    @classmethod
    def _make_multi(cls, geom_type, model_field):
        """
        Given the OGRGeomType for a geometry and its associated GeometryField,
        determine whether the geometry should be turned into a GeometryCollection.
        """
        return geom_type.num in cls.MULTI_TYPES and model_field.__class__.__name__ == "Multi%s" % geom_type.django

    def _verify_geom(self, geom):
        """
        Verify the geometry -- construct and return a GeometryCollection
        if necessary (for example if the model field is MultiPolygonField while
        the mapped shapefile only contains Polygons).
        """
        # Downgrade a 3D geom to a 2D one, if necessary.
        if self.model_field.dim != geom.coord_dim:
            geom.coord_dim = self.model_field.dim

        # Check if model_field is single geometry and geom is multiple. Raise
        if geom.geom_name.startswith("MULTI") and not self.model_field.geom_type.startswith("MULTI"):
            raise GDALException(
                f"Tried to convert multi geometry {geom.geom_name} single geometry {self.model_field.geom_type}."
            )

        if self._make_multi(geom.geom_type, self.model_field):
            # Constructing a multi-geometry type to contain the single geometry
            multi_type = self.MULTI_TYPES[geom.geom_type.num]
            g = OGRGeometry(multi_type, srs=geom.srs)
            g.add(geom)
        else:
            g = geom

        # Transforming the geometry with our Coordinate Transformation object.
        if geom.srs.srid != self.model_field.srid:
            g.transform(CoordTransform(source=geom.srs, target=SpatialReference(self.model_field.srid)))

        # Returning the WKT of the geometry.
        return g.ewkt

    def render(self, value, obj=None):
        """
        Returns an export representation of a GEOS object.

        Takes care of converting the object's field to a value that can be written to a spreadsheet.
        """
        return value.ewkt
