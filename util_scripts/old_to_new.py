# This script adapts the value of the old classification system to the new one, by filling the new columns in the
# expert_reportannotacion table category_id, complex_id and validation_value

# Old value - unclassified -> New value - unclassified
# All fields blank, status hidden or flagged (0 or -1) and some internal comment -> category_id = 1

# Old value - Definitely Aedes aegypti -> New value Aedes aegypti - Definitely
# aegypti_certainty_category = 2 tiger_certainty_category blank -> category_id = 5 category_value = 2

# Old value - Probably Aedes aegypti -> New value Aedes aegypti - Probably
# aegypti_certainty_category = 1 tiger_certainty_category blank -> category_id = 5 category_value = 1

# Old value - Definitely Aedes albopictus -> New value Aedes albopictus - Definitely
# tiger_certainty_category = 2 aegypti_certainty_category blank -> category_id = 4 category_value = 2

# Old value - Probably Aedes albopictus -> New value Aedes albopictus - Probably
# tiger_certainty_category = 1 aegypti_certainty_category blank -> category_id = 4 category_value = 1

# Old value - Not sure -> New value -> Not sure
# tiger_certainty_category = 0 aegypti_certainty_category = 0 -> category_id = 9

# Old value - Probably neither -> New value -> Other species
# tiger_certainty_category = -1 aegypti_certainty_category = -1 -> category_id = 2

# Old value - Definitely neither -> New value -> Other species
# tiger_certainty_category = -2 aegypti_certainty_category = -2 -> category_id = 2

# so...

import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

from tigacrafting.models import ExpertReportAnnotation, Categories


annotations = ExpertReportAnnotation.objects.filter(validation_complete=True)
n_annotations = len(annotations)
current = 1

c1 = Categories.objects.get(pk=1)
c5 = Categories.objects.get(pk=5)
c4 = Categories.objects.get(pk=4)
c9 = Categories.objects.get(pk=9)
c2 = Categories.objects.get(pk=2)

for r in ExpertReportAnnotation.objects.filter(validation_complete=True):
    r.category = None
    r.save(skip_lastmodified=True)
    print("Cleared {0} of {1}".format(current, n_annotations))
    current = current + 1

current = 1

for r in ExpertReportAnnotation.objects.filter(validation_complete=True):
    if r.report.type == 'adult':
        if r.aegypti_certainty_category is None and r.tiger_certainty_category is None:
            if r.user.groups.filter(name='expert').exists():
                r.category = c1
                r.save(skip_lastmodified=True)
            elif r.user.groups.filter(name='superexpert').exists():
                if r.revise:
                    r.category = c1
                    r.save(skip_lastmodified=True)
        elif r.aegypti_certainty_category == 2 and r.tiger_certainty_category is None:
            r.category = c5
            r.validation_value = ExpertReportAnnotation.VALIDATION_CATEGORY_DEFINITELY
            r.save(skip_lastmodified=True)
        elif r.aegypti_certainty_category == 1 and r.tiger_certainty_category is None:
            r.category = c5
            r.validation_value = ExpertReportAnnotation.VALIDATION_CATEGORY_PROBABLY
            r.save(skip_lastmodified=True)
        elif r.tiger_certainty_category == 2 and  r.aegypti_certainty_category is None:
            r.category = c4
            r.validation_value = ExpertReportAnnotation.VALIDATION_CATEGORY_DEFINITELY
            r.save(skip_lastmodified=True)
        elif r.tiger_certainty_category == 1 and r.aegypti_certainty_category is None:
            r.category = c4
            r.validation_value = ExpertReportAnnotation.VALIDATION_CATEGORY_PROBABLY
            r.save(skip_lastmodified=True)
        elif r.tiger_certainty_category == 0 and r.aegypti_certainty_category == 0:
            r.category = c9
            r.save(skip_lastmodified=True)
        elif r.tiger_certainty_category == -1 and r.aegypti_certainty_category == -1:
            r.category = c2
            r.save(skip_lastmodified=True)
        elif r.tiger_certainty_category == -2 and r.aegypti_certainty_category == -2:
            r.category = c2
            r.save(skip_lastmodified=True)
    print("Done {0} of {1}".format( current, n_annotations ))
    current = current + 1



