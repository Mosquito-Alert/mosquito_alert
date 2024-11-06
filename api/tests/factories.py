from django.utils import timezone

from tigaserver_app.models import Report, TigaUser

def create_report_object(user: TigaUser) -> Report:
    return Report(
        user=user,
        report_id=1234,  # TODO: change
        phone_upload_time=timezone.now(),
        creation_time=timezone.now(),
        version_time=timezone.now(),
        location_choice=Report.LOCATION_CURRENT,
        current_location_lon=2,
        current_location_lat=2,
    )