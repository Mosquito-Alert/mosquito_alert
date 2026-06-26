from django.contrib.gis.geos import Point

from mosquito_alert.geo.models import TemporaryBoundary


def create_boundary_contains_point(point: Point) -> TemporaryBoundary:
    polygon = point.buffer(
        0.01
    )  # Create a small buffer around the point to form a polygon
    boundary = TemporaryBoundary(geometry=polygon)
    boundary.save()
    return boundary
