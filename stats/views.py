from django.shortcuts import render
from django.db import connection
from tigaserver_app.models import *
from datetime import date, timedelta, datetime
import time
from collections import Counter
from tzlocal import get_localzone
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.cache import cache_page
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from tigacrafting.views import filter_reports
from tigaserver_project import settings
import json
from sets import Set
import datetime

@xframe_options_exempt
@cache_page(60 * 15)
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

def get_most_recently_validated_report(slug):
    completed_annot = ExpertReportAnnotation.objects.filter(validation_complete=True).filter(user__username=slug).extra(order_by=['-last_modified'])
    if len(completed_annot) > 0:
        latest_uncomplete_annotation = completed_annot.first()
        return latest_uncomplete_annotation.created
    return None

@api_view(['GET'])
def workload_pending_per_user(request):
    if request.method == 'GET':
        user_slug = request.QUERY_PARAMS.get('user_slug', -1)
        queryset = User.objects.all()
        user = get_object_or_404(queryset, username=user_slug)
        current_pending = ExpertReportAnnotation.objects.filter(user=user).filter(validation_complete=False).filter(report__type='adult')
        pending_detail = []
        for ano in current_pending:
            pending_detail.append({ 'report_id': ano.report_id, 'created': ano.report.creation_time.strftime('%d/%m/%Y - %H:%M:%S') })
        last_activity = get_most_recently_validated_report(user_slug)
        if last_activity is not None:
            pending = { 'current_pending_n' : current_pending.count(), 'current_pending': pending_detail, 'last_activity': last_activity.strftime('%d/%m/%Y') }
        else:
            pending = {'current_pending_n': current_pending, 'last_activity': 'Never'}
        return Response(pending)

@api_view(['GET'])
def workload_stats_per_user(request):
    if request.method == 'GET':
        user_slug = request.QUERY_PARAMS.get('user_slug', -1)
        tz = get_localzone()
        queryset = User.objects.all()
        user = get_object_or_404(queryset,username=user_slug)
        single_user_work_output = []
        annotated_reports = ExpertReportAnnotation.objects.filter(user=user).filter(validation_complete=True)
        ref_date = datetime(2014, 1, 1, 0, 0, 0, tzinfo=tz)
        end_date = tz.localize(datetime.now())
        while ref_date <= end_date:
            single_user_work_output.append([time.mktime(ref_date.timetuple())*1000, annotated_reports.filter(last_modified__year=ref_date.year).filter(last_modified__month=ref_date.month).filter(last_modified__day=ref_date.day).count()])
            ref_date += timedelta(hours=24)
        return Response(single_user_work_output)

@api_view(['GET'])
def workload_daily_report_input(request):
    if request.method == 'GET':
        tz = get_localzone()
        daily_report_input = []
        ref_date = datetime(2014, 1, 1, 0, 0, 0, tzinfo=tz)
        end_date = tz.localize(datetime.now())
        reports = Report.objects.all()
        while ref_date <= end_date:
            daily_report_input.append([time.mktime(ref_date.timetuple())*1000,reports.filter(phone_upload_time__year=ref_date.year).filter(phone_upload_time__month=ref_date.month).filter(phone_upload_time__day=ref_date.day).count()])
            ref_date += timedelta(hours=24)
        return Response(daily_report_input)

@api_view(['GET'])
def workload_available_reports(request):
    if request.method == 'GET':
        current_pending = Report.objects.exclude(creation_time__year=2014).exclude(note__icontains="#345").exclude(hide=True).exclude(photos=None).filter(type='adult').annotate(n_annotations=Count('expert_report_annotations')).filter(n_annotations=0)
        current_progress = Report.objects.exclude(creation_time__year=2014).exclude(note__icontains="#345").exclude(hide=True).exclude(photos=None).filter(type='adult').annotate(n_annotations=Count('expert_report_annotations')).filter(n_annotations__lt=3).exclude(n_annotations=0)
        user_id_filter = settings.USERS_IN_STATS
        overall_pending = ExpertReportAnnotation.objects.filter(user__id__in=user_id_filter).filter(validation_complete=False).filter(report__type='adult')
        current_pending = filter_reports(current_pending)
        current_progress = filter_reports(current_progress)
        data = { 'current_pending_n' : len(current_pending), 'current_progress_n' : len(current_progress), 'overall_pending': overall_pending.count()}
        return Response(data)


@login_required
def registration_stats(request):
    cursor = connection.cursor()
    cursor.execute("""
        select 
        count("user_UUID"), 
        extract(year from registration_time), 
        extract(month from registration_time) 
        from tigaserver_app_tigauser 
        group by extract(year from registration_time), extract(month from registration_time)
        order by 2,3
    """)
    registration = cursor.fetchall()

    now = datetime.datetime.now()
    current_year = now.year
    years = []

    for i in range(2014, current_year + 1):
        years.append(i)

    context = {'registration': json.dumps(registration), 'years': json.dumps(years), 'years_list': years}
    return render(request, 'stats/user_registration.html', context)


@login_required
def report_stats(request):
    cursor = connection.cursor()

    cursor.execute("""
        select count("version_UUID"), extract(year from server_upload_time), extract(month from server_upload_time) 
        from (
        select "version_UUID",server_upload_time from tigaserver_app_report where "version_UUID" in (select version_uuid from map_aux_reports where private_webmap_layer in ('mosquito_tiger_confirmed','mosquito_tiger_probable', 'yellow_fever_confirmed','yellow_fever_probable'))
        ) as t1
        group by extract(year from server_upload_time), extract(month from server_upload_time) 
        order by 2,3
    """)
    adults = cursor.fetchall()

    cursor.execute("""
        select count("version_UUID"), extract(year from server_upload_time), extract(month from server_upload_time) 
        from (
        select "version_UUID",server_upload_time from tigaserver_app_report where "version_UUID" in (select version_uuid from map_aux_reports where private_webmap_layer in ('storm_drain_dry','storm_drain_water'))
        ) as t1
        group by extract(year from server_upload_time), extract(month from server_upload_time) 
        order by 2,3
    """)
    sites = cursor.fetchall()
    now = datetime.datetime.now()
    current_year = now.year
    years = []

    for i in range(2014, current_year + 1):
        years.append(i)

    context = {'adults': json.dumps(adults), 'sites': json.dumps(sites), 'years': json.dumps(years), 'years_list': years}
    return render(request, 'stats/user_activity.html', context)


@login_required
def report_stats_ccaa_pie(request):
    cursor = connection.cursor()
    cursor.execute("""
        select count("version_UUID"), nomprov, code_hc, private_webmap_layer
        from 
        (
            (
            select *
            from
            map_aux_reports m,
            tigaserver_app_report r
            where private_webmap_layer in ('mosquito_tiger_confirmed','mosquito_tiger_probable','other_species','unidentified') AND
            m.version_uuid = r."version_UUID") r
            join
            provincies_4326 p
            on st_contains(p.geom,r.point)
        ) as t 
        group by nomprov, code_hc, private_webmap_layer order by 2, 4
    """)
    map_data = cursor.fetchall()

    cursor = connection.cursor()
    cursor.execute("""
        select count("version_UUID"), extract(year from observation_date), nomprov, code_hc, private_webmap_layer
        from 
        (
            (
            select *
            from
            map_aux_reports m,
            tigaserver_app_report r
            where private_webmap_layer in ('mosquito_tiger_confirmed','mosquito_tiger_probable','other_species','unidentified') AND
            m.version_uuid = r."version_UUID") r
            join
            provincies_4326 p
            on st_contains(p.geom,r.point)
        ) as t 
        group by nomprov, extract(year from observation_date), code_hc, private_webmap_layer order by 2, 3
    """)
    map_data_year = cursor.fetchall()

    context = { 'map_data': json.dumps(map_data), 'map_data_year': json.dumps(map_data_year) }
    return render(request, 'stats/report_stats_ccaa_pie.html', context)


@login_required
def report_stats_ccaa(request):
    cursor = connection.cursor()

    cursor.execute("""
        select
        cod_ccaa, nom_ccaa
        from comunitats_4326
    """)
    data_ccaa = cursor.fetchall()

    cursor.execute("""
    select cod_ccaa, ct, type, count("version_UUID")
    FROM
    (select c.cod_ccaa, r.type, ct, r."version_UUID"
    from
    (select *,extract(year from creation_time) as ct from tigaserver_app_report where "version_UUID" in (select version_uuid from map_aux_reports where private_webmap_layer in ('mosquito_tiger_confirmed','mosquito_tiger_probable', 'yellow_fever_confirmed','yellow_fever_probable','storm_drain_dry','storm_drain_water'))) r JOIN
    comunitats_4326 c
    on st_contains(c.geom,r.point)) as t 
    group by cod_ccaa, ct, type order by 3,2
    """)
    data = cursor.fetchall()

    years = Set()
    for elem in data:
        years.add(int(elem[1]))
    years = list(years)
    years.sort()


    # context = {'data': json.dumps(data), 'data_ccaa': json.dumps(data_ccaa),  'm_data': json.dumps(m_data), 'years': years}
    context = {'data': json.dumps(data), 'data_ccaa': json.dumps(data_ccaa), 'years': years}
    return render(request, 'stats/report_stats_ccaa.html', context)

@login_required
def workload_stats(request):
    this_user = request.user
    user_id_filter = settings.USERS_IN_STATS
    this_user_is_superexpert = this_user.groups.filter(name='superexpert').exists()
    if this_user_is_superexpert:
        users = User.objects.filter(groups__name='expert').filter(id__in=user_id_filter).order_by('first_name','last_name')
        context = {'users': users, 'load_everything_on_start': True}
        return render(request, 'stats/workload.html', context)
    else:
        return HttpResponse("You need to be logged in as superexpert to view this page. If you have have been recruited as an expert and have lost your log-in credentials, please contact MoveLab.")


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
