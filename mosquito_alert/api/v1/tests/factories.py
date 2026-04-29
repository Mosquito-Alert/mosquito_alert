from django.contrib.gis.geos import Point
from django.utils import timezone

from mosquito_alert.geo.models import TemporaryBoundary
from mosquito_alert.reports.models import Report
from mosquito_alert.users.models import TigaUser


def create_report_object(user: TigaUser) -> Report:
    return Report(
        user=user,
        report_id=1234,  # TODO: change
        phone_upload_time=timezone.now(),
        creation_time=timezone.now(),
        version_time=timezone.now(),
        location_choice=Report.LOCATION_CURRENT,
        current_location_lon=2.79036,
        current_location_lat=41.67419,
        note="Test report note",
    )


def create_boundary_contains_point(point: Point) -> TemporaryBoundary:
    polygon = point.buffer(
        0.01
    )  # Create a small buffer around the point to form a polygon
    boundary = TemporaryBoundary(geometry=polygon)
    boundary.save()
    return boundary
