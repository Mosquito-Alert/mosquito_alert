import random

from tigapublic.models import MapAuxReports
from tigaserver_app.models import Report, TigaUser

from api.tests.factories import create_report_object


def create_observation_object(user: TigaUser, is_published: bool = False) -> Report:
    report = create_report_object(user)
    report.type = Report.TYPE_ADULT
    report.save()

    if is_published:
        _ = MapAuxReports.objects.get_or_create(
            version_uuid=report,
            defaults={
                "id": random.randint(1, 2147483647),
                "user_id": user.pk,
                "ref_system": 4326,
                "type": report.type,
                "final_expert_status": 1,
                "visible": True,
            },
        )

    return report

