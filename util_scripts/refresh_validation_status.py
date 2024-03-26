import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path)

from django.core.wsgi import get_wsgi_application
from django.db.models import Q

application = get_wsgi_application()

from tigacrafting.models import Alert, AlertMetadata
from tigaserver_app.models import Report
import json

CATEGORY_ID_TO_IA_COLUMN = {
    '2': 'other_species',
    '4': 'albopictus',
    '5': 'aegypti',
    '6': 'japonicus',
    '7': 'koreicus',
    '8': 'japonicus-koreicus',
    '9': 'not_sure',
    '10': 'culex',
}

def main():
    report_alerts = Alert.objects.values('report_id')
    qs = Report.objects.filter(version_UUID__in=report_alerts)
    report_table = {}
    for r in qs:
        report_table[r.version_UUID] = json.loads(r.get_final_combined_expert_category_euro_struct_json())
    all_alerts = Alert.objects.all()
    for alert in all_alerts:
        try:
            alert_md = alert.alertmetadata
            alert_md.validation_status = not report_table[alert.report_id]['in_progress']
            try:
                alert_md.validation_species = CATEGORY_ID_TO_IA_COLUMN[report_table[alert.report_id]['category_id']]
            except KeyError:
                pass
            alert_md.save()
        except AlertMetadata.DoesNotExist:
            a = AlertMetadata(alert=alert,validation_status=not report_table[alert.report_id]['in_progress'])
            a.validation_status = not report_table[alert.report_id]['in_progress']
            try:
                a.validation_species = CATEGORY_ID_TO_IA_COLUMN[report_table[alert.report_id]['category_id']]
            except KeyError:
                pass
            a.save()


if __name__ == '__main__':
    main()