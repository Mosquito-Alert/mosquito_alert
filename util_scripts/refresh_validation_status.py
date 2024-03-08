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
            alert_md.save()
        except AlertMetadata.DoesNotExist:
            a = AlertMetadata(alert=alert,validation_status=not report_table[alert.report_id]['in_progress'])
            a.save()


if __name__ == '__main__':
    main()