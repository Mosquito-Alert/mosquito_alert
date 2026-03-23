from mosquito_alert.tigaserver_app.models import Report
from mosquito_alert.users.models import TigaUser

from mosquito_alert.api.v1.tests.factories import create_report_object


def create_breeding_site_object(user: TigaUser) -> Report:
    report = create_report_object(user)
    report.type = Report.TYPE_SITE
    report.breeding_site_type = Report.BreedingSiteType.STORM_DRAIN
    report.save()
    return report
