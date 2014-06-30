from django.shortcuts import render
from django.db.models import Q
from tigaserver_app.models import *
from datetime import date, timedelta, datetime
import time
from tzlocal import get_localzone
from django.views.decorators.clickjacking import xframe_options_exempt
from tigamap.views import get_latest_reports


@xframe_options_exempt
def show_usage(request):
    real_tigausers = TigaUser.objects.filter(registration_time__gte=date(2014, 6, 13))
    real_reports = get_latest_reports(Report.objects.filter(Q(package_name='Tigatrapp', creation_time__gte=date(2014, 6, 24)) |
                                                                 Q(package_name='ceab.movelab.tigatrapp',
                                                                   package_version__gt=3)))
    tz = get_localzone()
    ref_date = datetime(2014, 6, 13, 0, 0, 0,  tzinfo=tz)
    end_date = tz.localize(datetime.now())
    users = []
    site_reports = []
    adult_reports = []
    while ref_date <= end_date:
        site_reports.append({'date': time.mktime(ref_date.timetuple()), 'n': len([r for r in real_reports if r.type == 'site' and r.creation_time <= ref_date])})
        adult_reports.append({'date': time.mktime(ref_date.timetuple()), 'n': len([r for r in real_reports if r.type == 'adult' and r.creation_time <= ref_date])})
        users.append({'date': (time.mktime(ref_date.timetuple())), 'n': len(real_tigausers.filter(registration_time__lte=ref_date))})
        ref_date += timedelta(hours=1)
    # now set final day as current time
    site_reports.append({'date': time.mktime(end_date.timetuple()), 'n': len([r for r in real_reports if r.type == 'site' and r.creation_time <= ref_date])})
    adult_reports.append({'date': time.mktime(end_date.timetuple()), 'n': len([r for r in real_reports if r.type == 'adult' and r.creation_time <= ref_date])})
    users.append({'date': time.mktime(end_date.timetuple()), 'n': len(real_tigausers.filter(registration_time__lte=ref_date))})
    context = {'users': users, 'site_reports': site_reports, 'adult_reports': adult_reports}
    return render(request, 'stats/chart.html', context)


def show_fix_users(request):
    real_fixes = Fix.objects.filter(fix_time__gt='2014-06-13')
    tz = get_localzone()
    ref_date = datetime(2014, 6, 13, 0, 0, 0,  tzinfo=tz)
    end_date = tz.localize(datetime.now())
    users = []
    while ref_date <= end_date:
        users.append({'date': (time.mktime(ref_date.timetuple())), 'n': len(set(f.user_coverage_uuid for f in real_fixes.filter(fix_time_lte=ref_date)))})
        ref_date += timedelta(hours=1)
