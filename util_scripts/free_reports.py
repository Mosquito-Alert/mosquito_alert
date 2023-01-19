# This script frees already validated reports. Used mainly to prepare test databases
# coding=utf-8
import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path)

from tigaserver_app.models import Report, ExpertReportAnnotation


def report_is_validated(report):
    return ExpertReportAnnotation.objects.filter(report=report, user__groups__name='expert', validation_complete=True).count() == 3 and ExpertReportAnnotation.objects.filter(report=report, user__groups__name='superexpert', validation_complete=True).count() == 1

def free_report(report):
    ExpertReportAnnotation.objects.filter(report=report).delete()

def free_reports(number=10):
    reports = Report.objects.exclude(creation_time__year=2014).exclude(note__icontains="#345").exclude(photos__isnull=True).exclude(hide=True).filter(type='adult').order_by('-creation_time')
    i = 0
    for r in reports:
        if report_is_validated(r):
            free_report(r)
            print("Freeing report {0}, created on {1}".format( r.version_UUID, r.creation_time ))
            i +=1
            if i >= number:
                print("Reached limit")
                break

free_reports()