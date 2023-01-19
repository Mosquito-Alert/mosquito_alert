import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path + "util_scripts/")

from django.contrib.auth.models import User
from tigaserver_app.models import ExpertReportAnnotation
from django.db import connection


# this recovers only annotations with completed = True
def get_redundant_validations():
    sql = "select count(id),user_id, report_id from tigacrafting_expertreportannotation where validation_complete = true group by (user_id,report_id) having count(id) > 1 order by count(id) desc"
    cursor = connection.cursor()
    cursor.execute(sql)
    data = cursor.fetchall()
    return data

# this recovers annotations with completed = False
def get_redundant_annotations():
    sql = "select count(id),user_id, report_id from tigacrafting_expertreportannotation where validation_complete = false group by (user_id,report_id) having count(id) > 1 order by count(id) desc"
    cursor = connection.cursor()
    cursor.execute(sql)
    data = cursor.fetchall()
    return data

def remove_redundancy_for_not_validated(expert_id, report_id):
    annos = ExpertReportAnnotation.objects.filter(user=expert_id, report=report_id)
    #most recent
    keep_id = ExpertReportAnnotation.objects.filter(user=expert_id, report=report_id).order_by('-last_modified').first().id
    #delete all but most recent
    annos.exclude(id=keep_id).delete()


def remove_redundancy_for_validated(expert_id, report_id, superexperts):
    annos = ExpertReportAnnotation.objects.filter(user=expert_id,report=report_id)
    complete_exists = annos.filter(simplified_annotation=True).exists()
    keep_id = None
    if complete_exists:
        most_recent = annos.filter(simplified_annotation=True).order_by('-last_modified').first()
        keep_id = most_recent.id
    else:
        most_recent = annos.order_by('-last_modified').first()
        keep_id = most_recent.id
    for a in annos:
        if a.id != keep_id:
            a.delete()
    #also delete all superexpert annotations
    expert_annos = ExpertReportAnnotation.objects.filter(report=report_id).filter(user__in=superexperts)
    expert_annos.delete()


def main():
    redundant_validations = get_redundant_validations()
    superexperts = User.objects.filter(groups__name='superexpert').values('id').distinct()
    for d in redundant_validations:
        expert_id = d[1]
        report_id = d[2]
        remove_redundancy_for_validated(expert_id, report_id, superexperts)
    redundant_annotations = get_redundant_annotations()
    for r in redundant_annotations:
        expert_id = r[1]
        report_id = r[2]
        remove_redundancy_for_not_validated(expert_id,report_id)


if __name__ == "__main__":
    main()