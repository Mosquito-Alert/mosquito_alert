from tigaserver_app.models import Report, TigaUser

from api.tests.factories import create_report_object


def create_observation_object(user: TigaUser, is_published: bool = False) -> Report:
    report = create_report_object(user)
    report.type = Report.TYPE_ADULT
    report.save()

    if is_published:
        report.published_at = report.server_upload_time
    else:
        report.hide = True

    report.save()

    return report
