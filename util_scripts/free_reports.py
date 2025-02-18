# This script frees already validated reports. Used mainly to prepare test databases
# coding=utf-8
import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

from tigacrafting.models import IdentificationTask, ExpertReportAnnotation


def free_reports(number=10):
    for task in IdentificationTask.objects.done().order_by('-created_at')[:number]:
        print("Freeing report {0} created on {1}".format(task.report_id, task.created_at.pk))
        for annotation in ExpertReportAnnotation.objects.filter(identification_task=task):
            annotation.delete()

free_reports()