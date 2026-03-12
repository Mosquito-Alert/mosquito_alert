from mosquito_alert.tigaserver_app.models import Report, TigaUser

from mosquito_alert.api.v1.tests.factories import create_report_object


def create_bite_object(user: TigaUser) -> Report:
    report = create_report_object(user)
    report.type = Report.TYPE_BITE
    report.event_environment = Report.EVENT_ENVIRONMENT_INDOORS
    report.event_moment = Report.EVENT_MOMENT_NOW
    report.save()
    return report
