from django.shortcuts import render
from tigaserver_app.models import *
from django.db.models import Count, Min, Max
from datetime import date, timedelta


def show_usage(request):
    ref_date = date(2014, 5, 13)
    end_date = date.today()

    days = []
    users = []
    while ref_date < end_date:
        days.append(ref_date.strftime("%x"))
        ref_date += timedelta(days=1)
        users.append(len(TigaUser.objects.filter(registration_time__lt=ref_date)))
    context = {'days': days, 'users': users}
    return render(request, 'stats/chart.html', context)
