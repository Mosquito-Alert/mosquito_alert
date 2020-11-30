import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path + "util_scripts/")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()


import csv
import string
import random
from django.contrib.auth.models import User, Group
from tigaserver_app.models import EuropeCountry, Report, ExpertReportAnnotation, Categories
from django.conf import settings

# get list of all users
# for each user, get all annotations
# compare individual annotation with global consensus and write the result


def generate_expert_list():
    es_users = [User.objects.get(pk=i) for i in settings.USERS_IN_STATS]
    es_users.append(19)
    es_users.append(3)
    euro_users = [u for u in User.objects.filter(groups__name='eu_group_europe').all()]
    return es_users + euro_users


def revised_by_superexpert_set():
    revised = ExpertReportAnnotation.objects.filter(user__groups__name='superexpert', validation_complete=True, revise=True).distinct().values("report__version_UUID")
    a = [ r['report__version_UUID'] for r in revised ]
    return set(a)

def opinions_equal(opinion_1, opinion_2):
    if opinion_1.startswith("Other species") and opinion_2.startswith("Other species"):
        return True
    elif opinion_1 == opinion_2:
        return True
    return False


def main():
    all_users = generate_expert_list()
    all_annotations = 0
    revised_by_superexpert = revised_by_superexpert_set()
    headers = (['report_id','validated_by','validated_by_opinion','final_opinion','opinions_differ','revised_by_se'])
    with open('validation_data.csv', mode='w') as validation_data:
        validation_writer = csv.writer(validation_data, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        validation_writer.writerow(headers)
        for u in all_users:
            user_annotations = ExpertReportAnnotation.objects.filter(user=u).filter(validation_complete=True).exclude(report__creation_time__year=2014)
            for ano in user_annotations:
                if ano.report.latest_version and not ano.report.deleted and ano.report.hide == False and ano.report.get_is_expert_validated() == True and ano.report.type=='adult':
                    expert_opinion = ano.get_category_euro()
                    global_opinion = ano.report.get_final_combined_expert_category_euro()
                    all_annotations += 1
                    revised = ano.report.version_UUID in revised_by_superexpert
                    differ = not opinions_equal(expert_opinion, global_opinion)
                    validation_writer.writerow([ano.report.version_UUID, ano.user, expert_opinion, global_opinion, differ, revised])
    print(all_annotations)


if __name__ == "__main__":
    main()