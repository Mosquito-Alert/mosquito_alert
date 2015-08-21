from django.shortcuts import render
from django.db.models import Q
from tigaserver_app.models import *
from datetime import date, timedelta, datetime
import time
from collections import Counter
from tzlocal import get_localzone
from django.views.decorators.clickjacking import xframe_options_exempt, login_required


@xframe_options_exempt
@login_required
def show_usage(request):
    real_tigausers = TigaUser.objects.filter(registration_time__gte=date(2014, 6, 13))
    real_reports = Report.objects.filter(Q(package_name='Tigatrapp', creation_time__gte=date(2014, 6, 24)) | Q(package_name='ceab.movelab.tigatrapp', package_version__gt=3))
    tz = get_localzone()
    ref_date = datetime(2014, 6, 13, 0, 0, 0,  tzinfo=tz)
    end_date = tz.localize(datetime.now())
    users = []
    site_reports = []
    adult_reports = []
    while ref_date <= end_date:
        site_reports.append({'date': time.mktime(ref_date.timetuple()), 'n': real_reports.filter(type='site', creation_time__lte=ref_date).count()})
        adult_reports.append({'date': time.mktime(ref_date.timetuple()), 'n': real_reports.filter(type='adult', creation_time__lte=ref_date).count()})
        users.append({'date': (time.mktime(ref_date.timetuple())), 'n': real_tigausers.filter(registration_time__lte=ref_date).count()})
        ref_date += timedelta(hours=168)
    # now set final day as current time
    site_reports.append({'date': time.mktime(end_date.timetuple()), 'n': real_reports.filter(type='site', creation_time__lte=ref_date).count()})
    adult_reports.append({'date': time.mktime(end_date.timetuple()), 'n': real_reports.filter(type='adult', creation_time__lte=ref_date).count()})
    users.append({'date': time.mktime(end_date.timetuple()), 'n': real_tigausers.filter(registration_time__lte=ref_date).count()})
    context = {'users': users, 'site_reports': site_reports, 'adult_reports': adult_reports}
    return render(request, 'stats/chart.html', context)


def show_fix_users(request):
    real_fixes = Fix.objects.filter(fix_time__gt='2014-06-13')
    tz = get_localzone()
    ref_date = datetime(2014, 6, 13, 0, 0, 0,  tzinfo=tz)
    end_date = tz.localize(datetime.now())
    fix20_users = []
    fix15_users = []
    fix10_users = []
    fix5_users = []
    fix1_users = []

    while ref_date <= end_date:
        these_fixes = real_fixes.filter(fix_time__lte=ref_date, user_coverage_uuid__isnull=False)
        c = Counter(f.user_coverage_uuid for f in these_fixes)
        fix20_users.append({'date': (time.mktime(ref_date.timetuple())), 'n': len([k for k, v in c.iteritems() if v > 20])})
        fix15_users.append({'date': (time.mktime(ref_date.timetuple())), 'n': len([k for k, v in c.iteritems() if v > 15])})
        fix10_users.append({'date': (time.mktime(ref_date.timetuple())), 'n': len([k for k, v in c.iteritems() if v > 10])})
        fix5_users.append({'date': (time.mktime(ref_date.timetuple())), 'n': len([k for k, v in c.iteritems() if v > 5])})
        fix1_users.append({'date': (time.mktime(ref_date.timetuple())), 'n': len([k for k, v in c.iteritems() if v >= 1])})
        ref_date += timedelta(hours=24)
    context = {'fix20_users': fix20_users, 'fix15_users': fix15_users,'fix10_users': fix10_users, 'fix5_users': fix5_users, 'fix1_users': fix1_users}
    return render(request, 'stats/fix_user_chart.html', context)


def show_report_users(request):
    real_reports = [report for report in Report.objects.filter(Q(package_name='Tigatrapp', creation_time__gte=date(2014, 6, 24)) | Q(package_name='ceab.movelab.tigatrapp', package_version__gt=3)) if report.latest_version]
    tz = get_localzone()
    ref_date = datetime(2014, 6, 13,  tzinfo=tz)
    end_date = tz.localize(datetime.now())
    r0_users = []
    r1_users = []
    r2_users = []
    r3_users = []
    r4_users = []
    while ref_date <= end_date:
        these_reports = [r for r in real_reports if r.creation_time <= ref_date]
        c = Counter(r.user for r in these_reports)
        r0_users.append({'date': (time.mktime(ref_date.timetuple())), 'n': len([k for k, v in c.iteritems() if v > 0])})
        r1_users.append({'date': (time.mktime(ref_date.timetuple())), 'n': len([k for k, v in c.iteritems() if v > 1])})
        r2_users.append({'date': (time.mktime(ref_date.timetuple())), 'n': len([k for k, v in c.iteritems() if v > 2])})
        r3_users.append({'date': (time.mktime(ref_date.timetuple())), 'n': len([k for k, v in c.iteritems() if v > 3])})
        r4_users.append({'date': (time.mktime(ref_date.timetuple())), 'n': len([k for k, v in c.iteritems() if v > 4])})
        ref_date += timedelta(days=1)
    context = {'r0_users': r0_users, 'r1_users': r1_users, 'r2_users': r2_users, 'r3_users': r3_users, 'r4_users': r4_users}
    return render(request, 'stats/report_user_chart.html', context)
