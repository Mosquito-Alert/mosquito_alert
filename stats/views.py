from django.shortcuts import render
from django.db.models import Q
from tigaserver_app.models import *
from datetime import date, timedelta
from django.views.decorators.clickjacking import xframe_options_exempt
from tigamap.views import get_latest_reports


@xframe_options_exempt
def show_usage(request):
    real_tigausers = TigaUser.objects.filter(registration_time__gte=date(2014, 6, 5))
    real_reports = get_latest_reports(Report.objects.filter(Q(package_name='Tigatrapp', package_version__gt=0) |
                                                                 Q(package_name='ceab.movelab.tigatrapp',
                                                                   package_version__gt=3)))
    ref_date = date(2014, 6, 13)
    end_date = date.today()
    days = []
    users = []
    site_reports = []
    adult_reports = []
    while ref_date <= end_date:
        days.append(ref_date.strftime("%x"))
        ref_date += timedelta(days=1)
        users.append(len(real_tigausers.filter(registration_time__lte=ref_date)))
        site_reports.append(len([r for r in real_reports if r.type == 'site' and r.creation_time.date() <= ref_date]))
        adult_reports.append(len([r for r in real_reports if r.type == 'adult' and r.creation_time.date() <= ref_date]))
    context = {'days': days, 'users': users, 'site_reports': site_reports, 'adult_reports': adult_reports}
    return render(request, 'stats/chart.html', context)
