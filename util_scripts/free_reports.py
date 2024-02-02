# This script frees already validated reports. Used mainly to prepare test databases
# coding=utf-8
import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

from tigaserver_app.models import Report, ExpertReportAnnotation
from django.db.models import Count


def free_report(report):
    ExpertReportAnnotation.objects.filter(report=report).delete()

def free_reports(number=10):
    reports = Report.objects.queueable().with_finished_validation(state=False).filter(type='adult').order_by('-server_upload_time')
    i = 0
    for r in reports:
        free_report(r)
        print("Freeing report {0}, created on {1}".format(r.pk, r.creation_time))
        i +=1
        if i >= number:
            print("Reached limit")
            break

free_reports()