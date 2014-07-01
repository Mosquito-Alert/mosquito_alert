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
        ref_date += timedelta(hours=4)
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
    fix1000_users = []
    fix500_users = []
    fix250_users = []
    fix100_users = []
    fix1_users = []

    while ref_date <= end_date:
        these_fixes = real_fixes.filter(fix_time__lte=ref_date)
        these_users = set(f.user_coverage_uuid for f in these_fixes)
        usertable = []
        for this_user in these_users:
            usertable.append({'user': this_user, 'n': these_fixes.filter(user_coverage_uuid=this_user).count()})
        fix1000_users.append({'date': (time.mktime(ref_date.timetuple())), 'n': len(set(u.user for u in usertable if u.n > 1000))})
        fix500_users.append({'date': (time.mktime(ref_date.timetuple())), 'n': len(set(u.user for u in usertable if u.n > 500))})
        fix250_users.append({'date': (time.mktime(ref_date.timetuple())), 'n': len(set(u.user for u in usertable if u.n > 250))})
        fix100_users.append({'date': (time.mktime(ref_date.timetuple())), 'n': len(set(u.user for u in usertable if u.n > 100))})
        fix1_users.append({'date': (time.mktime(ref_date.timetuple())), 'n': len(set(u.user for u in usertable if u.n > 1))})
        ref_date += timedelta(hours=24)
    context = {'fix1000_users': fix1000_users, 'fix500_users': fix500_users,'fix250_users': fix250_users, 'fix100_users': fix100_users,'fix1_users': fix1_users}
    return render(request, 'stats/fix_user_chart.html', context)


def show_report_users(request):
    real_tigausers = TigaUser.objects.filter(registration_time__gte=date(2014, 6, 13))
    tz = get_localzone()
    ref_date = datetime(2014, 6, 13,  tzinfo=tz)
    end_date = tz.localize(datetime.now())
    r100_users = []
    r50_users = []
    r10_users = []
    r1_users = []
    r0_users = []
    while ref_date <= end_date:
        these_users = real_tigausers.filter(registration_time__lte=ref_date)
        r0_users.append({'date': (time.mktime(ref_date.timetuple())), 'n': these_users.count()})
        r1_users.append({'date': (time.mktime(ref_date.timetuple())), 'n': len(set(u for u in these_users if u.n_reports >= 1))})
        r10_users.append({'date': (time.mktime(ref_date.timetuple())), 'n': len(set(u for u in these_users if u.n_reports > 10))})
        r50_users.append({'date': (time.mktime(ref_date.timetuple())), 'n': len(set(u for u in these_users if u.n_reports > 50))})
        r100_users.append({'date': (time.mktime(ref_date.timetuple())), 'n': len(set(u for u in these_users if u.n_reports > 100))})
        ref_date += timedelta(days=1)
    context = {'r100_users': r100_users, 'r50_users': r50_users, 'r10_users': r10_users, 'r1_users': r1_users, 'r0_users': r0_users}
    return render(request, 'stats/report_user_chart.html', context)
