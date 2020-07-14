import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path + "util_scripts/")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()


from django.db.models import Count
from tigaserver_app.models import EuropeCountry, Report, ExpertReportAnnotation, Categories


current_progress = Report.objects.exclude(creation_time__year=2014).exclude(note__icontains="#345").exclude(hide=True).exclude(photos=None).filter(type='adult').annotate(n_annotations=Count('expert_report_annotations')).filter(n_annotations__lt=3).exclude(n_annotations=0).order_by('-server_upload_time')
reports_filtered = filter(lambda x: not x.deleted and x.latest_version, current_progress)
for c in current_progress:
    country = 'None'
    if c.country is not None:
        country = c.country.name_engl
    print("Report in progress {0} - country {1} - date {2}".format(c.version_UUID, country, c.server_upload_time  ))
    assigned_to = ExpertReportAnnotation.objects.filter(report=c)
    for a in assigned_to:
        print("\t - assigned to {0} from country , regional manager , country has regional manager ".format( a.user.username ))