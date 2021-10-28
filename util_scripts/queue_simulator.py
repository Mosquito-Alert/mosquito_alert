import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

from tigacrafting.models import ExpertReportAnnotation, UserStat
from tigaserver_app.models import Report, EuropeCountry
from django.contrib.auth.models import User, Group
from django.db.models import Q, ExpressionWrapper
from django.db.models import Count
from django.db.models import F
from django.db.models import DateTimeField
import datetime

max_given = 5


def get_countries_with_national_supervisor():
    country_with_supervisor = UserStat.objects.filter(national_supervisor_of__isnull=False).values('national_supervisor_of__gid').distinct()
    countries = EuropeCountry.objects.filter(gid__in=country_with_supervisor)
    return countries


def get_countries_without_national_supervisor():
    country_with_supervisor = get_countries_with_national_supervisor()
    return EuropeCountry.objects.exclude(gid__in=country_with_supervisor)


def get_regional_supervisors_days_to_free_report():
    national_supervisors = UserStat.objects.filter(national_supervisor_of__isnull=False)


def get_global_queue_regular_user(this_user):
    current_pending = ExpertReportAnnotation.objects.filter(user=this_user).filter(validation_complete=False).filter(report__type='adult').count()
    my_reports = ExpertReportAnnotation.objects.filter(user=this_user).filter(report__type='adult').values('report').distinct()

    new_reports_unfiltered = Report.objects.exclude(creation_time__year=2014).exclude(note__icontains="#345").exclude(version_UUID__in=my_reports).exclude(photos__isnull=True).exclude(hide=True).filter(type='adult').annotate(n_annotations=Count('expert_report_annotations')).filter(n_annotations__lt=max_given)

    bounding_boxes = EuropeCountry.objects.filter(is_bounding_box=True)

    #reports without country and reports from country without national supervisor
    countries_without_national_supervisor = get_countries_without_national_supervisor()
    by_country_unfiltered = new_reports_unfiltered.filter( Q(country__isnull=True) | Q(country__in=countries_without_national_supervisor) ).exclude( country__in = bounding_boxes )

    #reports conceded by national supervisors
    # obtain list of threshold date for all countries with supervisor
    # for each country and threshold date, obtain list of reports
    countries_with_national_supervisor = get_countries_with_national_supervisor()
    expired = None
    for country in countries_with_national_supervisor:
        reports_in_country = new_reports_unfiltered.filter(country=country)
        threshold_date_expression = ExpressionWrapper( F('server_upload_time') + datetime.timedelta(days=country.national_supervisor_report_expires_in), output_field=DateTimeField() )
        reports_expired_country = reports_in_country.annotate(threshold_date=threshold_date_expression).filter( threshold_date__lte=datetime.datetime.now() )
        if expired is None:
            expired = reports_expired_country
        else:
            expired = expired | reports_expired_country

    reports_in_queue = expired | by_country_unfiltered
    return reports_in_queue.order_by('-server_upload_time')


this_user = User.objects.get(pk=115)
queue = get_global_queue_regular_user(this_user)
print(len(queue))




