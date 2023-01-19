# coding=utf-8
import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path)

from django.contrib.auth.models import User
from tigaserver_app.models import ExpertReportAnnotation, Report

def check_assign_report_to_users(experts, national_supervisor, report):
    #queue not full for experts
    for expert in experts:
        anno_expert = ExpertReportAnnotation.objects.filter(validation_complete=False,user=expert)
        if anno_expert.count() >= 5:
            print("Expert {0} has full report queue".format( expert.username ))
            return False

    #queue not full for n supervisor
    anno_supervisor = ExpertReportAnnotation.objects.filter(validation_complete=False,user=national_supervisor)
    if anno_supervisor.count() >= 5:
        print("National supervisor {0} has full report queue".format(national_supervisor.username))
        return False

    #not already assigned
    for expert in experts:
        anno_expert_current_report = ExpertReportAnnotation.objects.filter(report=report)
        if anno_expert_current_report.exists():
            print("Expert {0} has already been assigned the report".format( expert.username ))
            return False

    anno_supervisor_current_report = ExpertReportAnnotation.objects.filter(report=report)
    if anno_supervisor_current_report.exists():
        print("National {0} has already been assigned the report".format(expert.username))
        return False

    return True


def main():
    report = Report.objects.get(pk='c7021184-db0e-490c-97b1-7e41073ca7f4')
    expert_1 = User.objects.get(pk=120) #o.mikov
    expert_2 = User.objects.get(pk=105) #f.gunay
    ns = User.objects.get(pk=145) #a.ibanez
    super_reritja = User.objects.get(pk=25)

    experts = [expert_1, expert_2]

    if check_assign_report_to_users(experts, ns, report):
        print("Checks ok!")
    else:
        print("Some problems!")
        sys.exit(1)

    for expert in experts:
        new_annotation = ExpertReportAnnotation(report=report, user=expert)
        new_annotation.simplified_annotation = True
        new_annotation.save()

    new_annotation = ExpertReportAnnotation(report=report, user=ns)
    new_annotation.simplified_annotation = False
    new_annotation.save()

    new_annotation = ExpertReportAnnotation(report=report, user=super_reritja)
    new_annotation.save()


if __name__ == "__main__":
    main()