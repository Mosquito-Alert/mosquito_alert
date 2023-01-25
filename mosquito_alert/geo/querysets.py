from django.contrib.gis.db.models.functions import Area
from django.contrib.gis.db.models.functions import Distance as DistanceFunction
from django.contrib.gis.geos import Point, Polygon
from django.contrib.gis.geos.collections import MultiPoint, MultiPolygon
from django.contrib.gis.measure import Distance as DistanceMeasure
from django.db.models import F, Q, QuerySet
from polymorphic.managers import PolymorphicQuerySet
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
    def __init__(self, field_prefix=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.field_prefix = field_prefix + "__" if field_prefix else ""

    def filter_by_boundary(self, boundaries, include_descendants=False):

        if not isinstance(boundaries, (list, tuple)):
            boundaries = [boundaries]

        if include_descendants:
            for b in boundaries:
                if descendats := list(b.get_descendants()):
                    boundaries += descendats

        return self.filter(**{f"{self.field_prefix}boundaries__in": boundaries})

    def filter_by_polygon_intersection(self, polygon, negate=False):
        func = self.filter
        if negate:
            func = self.exclude

        return func(**{f"{self.field_prefix}point__intersects": polygon})

    def first_by_distance(self, point):
        return self.order_by_distance(point=point).first()

    def order_by_distance(self, point):
        return self.annotate(
            distance=DistanceFunction(f"{self.field_prefix}point", point)
        ).order_by("distance")

    def within_circle(self, center_point, radius_meters):
        return self.filter(
            **{
                f"{self.field_prefix}point__dwithin": (
                    center_point,
                    DistanceMeasure(m=radius_meters),
                )
            }
        )


class GeoLocatedModelQuerySet(LocationQuerySet):
    # NOTE: do not use *args, **kwargs. Error when using polymorphic querysets.
    def __init__(
        self,
        model=None,
        query=None,
        using=None,
        hints=None,
        location_fk_field="location",
    ):
        super().__init__(
            model=model,
            query=query,
            using=using,
            hints=hints,
            field_prefix=location_fk_field,
        )


class GeoLocatedPolymorphicModelQuerySet(PolymorphicQuerySet, GeoLocatedModelQuerySet):
    pass
