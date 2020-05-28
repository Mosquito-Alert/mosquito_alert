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
from tigaserver_app.models import EuropeCountry, Report, ExpertReportAnnotation


def exclude_row(new_class, old_class):
    if new_class == "Other species" and old_class == "Definitely not albopictus or aegypti":
        return True
    if new_class == "Other species" and old_class == "Probably neither albopictus nor aegypti":
        return True
    return False


def write_classif_data_to_disk(data):
    with open('classif_data.csv', mode='w') as classif_check:
        classif_writer = csv.writer(classif_check, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for k in data.keys():
            classif_writer.writerow([k, data[k]['new_class'],data[k]['old_class']])

def read_classification_data_from_file():
    classif = {}
    with open('classif_data.csv', mode='r') as classif_check:
        classif_reader = csv.reader(classif_check, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for row in classif_reader:
            classif[row[0]] = {'new_class': row[1],'old_class': row[2]}
    return classif

def read_classification_data_from_db():
    classif = {}
    for r in Report.objects.filter(type='adult'):
        if ExpertReportAnnotation.objects.filter(report=r, user__groups__name='expert', validation_complete=True, category__isnull=False).count() >= 3:
            new_class = r.get_final_combined_expert_category_euro()
            old_class = r.get_final_combined_expert_category()
            if not exclude_row(new_class,old_class) and new_class != old_class:
                classif[r.version_UUID] = {'new_class': r.get_final_combined_expert_category_euro(), 'old_class': r.get_final_combined_expert_category()}
    return classif


def crunch():
    classif = read_classification_data_from_file()
    for k in classif.keys():
        n = ExpertReportAnnotation.objects.filter(report__version_UUID=k, user__groups__name='superexpert', validation_complete=True).count()
        if n > 1:
            print("Superexpert validations for report {0} - {1}".format(k,n))

    # classif = read_classification_data_from_db()
    # for k in classif.keys():
    #     n = ExpertReportAnnotation.objects.filter(report__version_UUID=k, user__groups__name='superexpert', validation_complete=True).count()
    #     print("Report {0} superexpert annotations {1}".format( k, n ))


crunch()