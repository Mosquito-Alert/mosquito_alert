import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path + "util_scripts/")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

from tigacrafting.models import IdentificationTask, ExpertReportAnnotation

for task in IdentificationTask.objects.ongoing().select_related('report', 'report__country').order_by('report__server_upload_time'):
    print("Report in progress {0} - country {1} - date {2}".format(task.report_id, task.report.country, task.created_at))
    assigned_to = ExpertReportAnnotation.objects.filter(identification_task=task).values_list('user__username', flat=True)
    print("\t - assigned to {0} from country , regional manager , country has regional manager ".format(assigned_to))