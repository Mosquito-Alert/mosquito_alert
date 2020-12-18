import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path + "util_scripts/")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

from tigaserver_app.models import *
from datetime import date, timedelta, datetime
import time
from tzlocal import get_localzone
import datetime
import csv

def write_csv_file(filename,dict_data,csv_columns):
    with open(filename, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
        writer.writeheader()
        for data in dict_data:
            writer.writerow(data)


def get_data():
    real_tigausers = TigaUser.objects.filter(registration_time__gte=date(2014, 6, 13))
    real_reports = Report.objects.filter(Q(package_name='Tigatrapp', creation_time__gte=date(2014, 6, 24)) | Q(package_name='ceab.movelab.tigatrapp', package_version__gt=3))
    tz = get_localzone()
    ref_date = datetime.datetime(2014, 6, 13, 0, 0, 0,  tzinfo=tz)
    end_date = tz.localize(datetime.datetime.now())
    users = []
    site_reports = []
    adult_reports = []
    while ref_date <= end_date:
        # site_reports.append({'date': time.mktime(ref_date.timetuple()), 'n': real_reports.filter(type='site', creation_time__lte=ref_date).count()})
        # adult_reports.append({'date': time.mktime(ref_date.timetuple()), 'n': real_reports.filter(type='adult', creation_time__lte=ref_date).count()})
        # users.append({'date': (time.mktime(ref_date.timetuple())), 'n': real_tigausers.filter(registration_time__lte=ref_date).count()})
        site_reports.append({'date': ref_date.isoformat(),'n': real_reports.filter(type='site', creation_time__lte=ref_date).count()})
        adult_reports.append({'date': ref_date.isoformat(),'n': real_reports.filter(type='adult', creation_time__lte=ref_date).count()})
        users.append({'date': ref_date.isoformat(),'n': real_tigausers.filter(registration_time__lte=ref_date).count()})
        ref_date += timedelta(hours=168)
    # now set final day as current time
    # site_reports.append({'date': time.mktime(end_date.timetuple()), 'n': real_reports.filter(type='site', creation_time__lte=ref_date).count()})
    # adult_reports.append({'date': time.mktime(end_date.timetuple()), 'n': real_reports.filter(type='adult', creation_time__lte=ref_date).count()})
    # users.append({'date': time.mktime(end_date.timetuple()), 'n': real_tigausers.filter(registration_time__lte=ref_date).count()})
    site_reports.append({'date': end_date.isoformat(), 'n': real_reports.filter(type='site', creation_time__lte=ref_date).count()})
    adult_reports.append({'date': end_date.isoformat(), 'n': real_reports.filter(type='adult', creation_time__lte=ref_date).count()})
    users.append({'date': end_date.isoformat(), 'n': real_tigausers.filter(registration_time__lte=ref_date).count()})

    write_csv_file('/tmp/site_reports.csv',site_reports,['date','n'])
    write_csv_file('/tmp/adult_reports.csv', adult_reports, ['date', 'n'])
    write_csv_file('/tmp/users.csv', users, ['date', 'n'])


get_data()