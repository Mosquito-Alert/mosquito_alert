import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path + "util_scripts/")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from tigaserver_app.models import ExpertReportAnnotation
from django.core.mail import send_mail


def format_annotations(wrong_annotations):
    retVal = ''
    retVal += 'Wrong annotations:\n'
    for r in wrong_annotations:
        retVal += 'Annotation id - {0} / Category - {1}'.format( r.id, r.category, ) + '\n'
    return retVal


def send_email(wrong_annotations):
    body = format_annotations(wrong_annotations)
    send_mail('[MA] - Incorrect movelab annotations', body, 'a.escobar@creaf.uab.cat', ['a.escobar@creaf.uab.cat'], fail_silently=False, )


def check_validations():
    base_qs = ExpertReportAnnotation.objects.filter(category__specify_certainty_level=True).filter(validation_complete=True).filter(validation_value__isnull=True)
    incorrect_annotations = base_qs.count()
    if incorrect_annotations > 0:
        wrong_annotations = [ r for r in base_qs ]
        send_email(wrong_annotations)
    for ano in base_qs:
        ano.validation_value = 1
        ano.save()


if __name__ == "__main__":
    check_validations()