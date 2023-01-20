from django.contrib.gis.gdal import (
    CoordTransform,
    OGRGeometry,
    OGRGeomType,
    SpatialReference,
)
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
        Returns an appropriate Python object for an imported value.

        For example, if you import a value from a spreadsheet,
        :meth:`~import_export.widgets.Widget.clean` handles conversion
        of this value into the corresponding Python object.

        Numbers or dates can be *cleaned* to their respective data types and
        don't have to be imported as Strings.
        """
        return GEOSGeometry(self.verify_geom(geom=value))

    @classmethod
    def make_multi(cls, geom_type, model_field):
        """
        Given the OGRGeomType for a geometry and its associated GeometryField,
        determine whether the geometry should be turned into a GeometryCollection.
        """
        return (
            geom_type.num in cls.MULTI_TYPES
            and model_field.__class__.__name__ == "Multi%s" % geom_type.django
        )

    def verify_geom(self, geom):
        """
        Verify the geometry -- construct and return a GeometryCollection
        if necessary (for example if the model field is MultiPolygonField while
        the mapped shapefile only contains Polygons).
        """
        # Downgrade a 3D geom to a 2D one, if necessary.
        if self.model_field.dim != geom.coord_dim:
            geom.coord_dim = self.model_field.dim

        if self.make_multi(geom.geom_type, self.model_field):
            # Constructing a multi-geometry type to contain the single geometry
            multi_type = self.MULTI_TYPES[geom.geom_type.num]
            g = OGRGeometry(multi_type)
            g.add(geom)
        else:
            g = geom

        # Transforming the geometry with our Coordinate Transformation object.

        g.transform(
            CoordTransform(
                source=geom.srs, target=SpatialReference(self.model_field.srid)
            )
        )

        # Returning the WKT of the geometry.
        return g.wkt

    def render(self, value, obj=None):
        """
        Returns an export representation of a Python value.

        For example, if you have an object you want to export,
        :meth:`~import_export.widgets.Widget.render` takes care of converting
        the object's field to a value that can be written to a spreadsheet.
        """
        return value.wkt
