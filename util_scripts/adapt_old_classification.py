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


def exclude_row(new_class, old_class):
    if new_class == "Other species" and old_class == "Definitely not albopictus or aegypti":
        return True
    if new_class == "Other species" and old_class == "Probably neither albopictus nor aegypti":
        return True
    return False


def write_classif_data_to_disk(data, filename):
    with open(filename, mode='w') as classif_check:
        classif_writer = csv.writer(classif_check, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for k in data.keys():
            classif_writer.writerow([k, data[k]['new_class'],data[k]['old_class']])

def read_classification_data_from_file(filename):
    classif = {}
    with open(filename, mode='r') as classif_check:
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


def translate(old_class):
    if old_class == 'Not sure':
        new_category = Categories.objects.get(pk=9)
        return { "new_category": new_category, "new_value": None, "tiger_certainty_category": 0, "aegypti_certainty_category": 0  }
    elif old_class == 'Probably Aedes albopictus':
        new_category = Categories.objects.get(pk=4)
        return {"new_category": new_category, "new_value": 1, "tiger_certainty_category": 1, "aegypti_certainty_category": -1}
    elif old_class == 'Definitely Aedes albopictus':
        new_category = Categories.objects.get(pk=4)
        return {"new_category": new_category, "new_value": 2, "tiger_certainty_category": 2, "aegypti_certainty_category": -2}
    elif old_class == 'Definitely not albopictus or aegypti':
        new_category = Categories.objects.get(pk=2)
        return {"new_category": new_category, "new_value": None, "tiger_certainty_category": -2, "aegypti_certainty_category": -2}
    elif old_class == 'Probably Aedes aegypti':
        new_category = Categories.objects.get(pk=5)
        return {"new_category": new_category, "new_value": 1, "tiger_certainty_category": -1, "aegypti_certainty_category": 1}
    elif old_class == 'Probably neither albopictus nor aegypti':
        new_category = Categories.objects.get(pk=2)
        return {"new_category": new_category, "new_value": None, "tiger_certainty_category": -1, "aegypti_certainty_category": -1}
    else:
        raise Exception("Unknown old class {0}".format(old_class,))


def do_revise(anno, old_class):
    translation_struct = translate(old_class)
    new_category = translation_struct['new_category']
    anno.category = new_category
    anno.validation_value = translation_struct['new_value']
    anno.tiger_certainty_category = translation_struct['tiger_certainty_category']
    anno.aegypti_certainty_category = translation_struct['aegypti_certainty_category']
    anno.revise = True
    #anno.save()
    return anno


def create_revision(report_id, old_class):
    r = Report.objects.get(pk=report_id)
    super_movelab = User.objects.get(pk=24)
    e = ExpertReportAnnotation()
    e.report = r
    e.user = super_movelab
    return do_revise(e, old_class)


def revise_existing_ack(report_id, old_class):
    superexpert_anno = ExpertReportAnnotation.objects.filter(report__version_UUID=report_id, user__groups__name='superexpert', validation_complete=True, revise=False).first()
    return do_revise(superexpert_anno,old_class)


def revise_multiple_ack(report_id, old_class):
    super_movelab_anno = ExpertReportAnnotation.objects.filter(report__version_UUID=report_id, user__groups__name='superexpert', validation_complete=True, revise=False, user__id=24).first()
    if super_movelab_anno is not None:
        return do_revise(super_movelab_anno, old_class)
    else:
        super_reritja_anno = ExpertReportAnnotation.objects.filter(report__version_UUID=report_id, user__groups__name='superexpert', validation_complete=True, revise=False, user__id=25).first()
        if super_reritja_anno is not None:
            return do_revise(super_movelab_anno, old_class)
        else:
            first_anno = ExpertReportAnnotation.objects.filter(report__version_UUID=report_id, user__groups__name='superexpert', validation_complete=True, revise=False).first()
            return do_revise(first_anno, old_class)


def crunch():

    classif = read_classification_data_from_db()
    write_classif_data_to_disk(classif,'classif_data_v2.csv')

    '''
    classif = read_classification_data_from_file('classif_data.csv')
    n = 0
    s = set()
    new_annos = []
    revised_annos = []
    n_multiple_revisions = 0
    for k in classif.keys():
        report_id = k
        old_class = classif[k]['old_class']
        new_class = classif[k]['new_class']

        n_ack = ExpertReportAnnotation.objects.filter(report__version_UUID=k, user__groups__name='superexpert', validation_complete=True, revise=False).count()
        n_rev = ExpertReportAnnotation.objects.filter(report__version_UUID=k, user__groups__name='superexpert', validation_complete=True, revise=True).count()

        #if old_class == 'Not sure' and new_class == 'Probably Aedes albopictus':
        if n_rev == 0:              #No revisions
            if n_ack > 0:           #Acknowledged by some superexpert
                if n_ack == 1:      #Acknowledged by just one superexpert
                    revised_annos.append(revise_existing_ack(report_id, old_class))
                elif n_ack > 1:     #Acknowledged by several superexperts
                    revised_annos.append(revise_multiple_ack(report_id, old_class))
            else:                   #Acknowledged by no one
                new_annos.append(create_revision(report_id, old_class))
        else:                       #Some revisions
            n_multiple_revisions += 1
            if n_rev == 1:          #Exactly one revision
                pass
            elif n_rev > 1:         #More than one revision
                pass

    print("New annotations: {0}".format(len(new_annos)))
    print("Revised annotations: {0}".format(len(revised_annos)))
    print("Multiple revisions: {0}".format(str(n_multiple_revisions)))

    for anno in new_annos:
        anno.save()

    for anno in revised_annos:
        anno.save()
    '''


    # classif = read_classification_data_from_file()
    # for k in classif.keys():
    #     n = ExpertReportAnnotation.objects.filter(report__version_UUID=k, user__groups__name='superexpert', validation_complete=True).count()
    #     if n > 1:
    #         print("Superexpert validations for report {0} - {1}".format(k,n))

    # classif = read_classification_data_from_db()
    # for k in classif.keys():
    #     n = ExpertReportAnnotation.objects.filter(report__version_UUID=k, user__groups__name='superexpert', validation_complete=True).count()
    #     print("Report {0} superexpert annotations {1}".format( k, n ))


crunch()