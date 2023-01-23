from django.contrib.gis.db.models.functions import Area
from django.contrib.gis.db.models.functions import Distance as DistanceFunction
from django.contrib.gis.geos import Point, Polygon
from django.contrib.gis.geos.collections import MultiPoint, MultiPolygon
from django.contrib.gis.measure import Distance as DistanceMeasure
from django.db.models import F, Q, QuerySet
from treebeard.mp_tree import MP_NodeQuerySet


class BoundaryQuerySet(MP_NodeQuerySet):
    def have_boundary_layer_conflicts(self):
        # Conflict is considered when:
        #    Diff boundary.depth and boundary_layer.depth
        return self.filter(~Q(boundary_layer__depth=F("depth")))

    def first_by_area(self):
        return (
            self.annotate(area=Area("geometry_model__geometry")).order_by("area").last()
        )

    def prefetch_geometry(self):
        return self.prefetch_related("geometry_model")

    def reverse_geocoding(self, point):

        if not isinstance(point, (Point, MultiPoint)):
            raise ValueError("Only point geometries are supported.")

        return self.filter(geometry_model__geometry__intersects=point)

    def reverse_polygon_geocoding(self, polygon):

        if not isinstance(polygon, (Polygon, MultiPolygon)):
            raise ValueError("Only polygon geometries are supported.")

        point = polygon.point_on_surface
        if isinstance(polygon, MultiPolygon):
            point = MultiPoint([x.point_on_surface for x in polygon])

        return self.reverse_geocoding(point=point)


class LocationQuerySet(QuerySet):
    def __init__(self, point_field_name="point", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.point_field_name = point_field_name

    def filter_by_polygon_intersection(self, polygon, negate=False):
        func = self.filter
        if negate:
            func = self.exclude

        return func(**{f"{self.point_field_name}__intersects": polygon})

    def first_by_distance(self, point):
        return self.order_by_distance(point=point).first()

    def order_by_distance(self, point):
        return self.annotate(
            distance=DistanceFunction(self.point_field_name, point)
        ).order_by("distance")

    def within_circle(self, center_point, radius_meters):
        return self.filter(
            **{
                f"{self.point_field_name}__dwithin": (
                    center_point,
                    DistanceMeasure(m=radius_meters),
                )
            }
        )


class GeoLocatedModelQuerySet(LocationQuerySet):
    def __init__(self, location_fk_field="location", *args, **kwargs):
        super().__init__(
            point_field_name=f"{location_fk_field}__point", *args, **kwargs
        )
