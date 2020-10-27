from django.shortcuts import render, redirect
from django.db import connection
from tigaserver_app.models import *
from tigacrafting.models import UserStat
from datetime import date, timedelta, datetime
import time
import pytz
from collections import Counter
from tzlocal import get_localzone
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.cache import cache_page
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view,permission_classes
from rest_framework.response import Response
from tigacrafting.views import filter_reports
from tigaserver_project import settings
import json
import datetime
from django.utils import timezone
from tigascoring.xp_scoring import compute_user_score_in_xp_v2, get_ranking_data
from rest_framework.exceptions import ParseError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import math
from django.utils import translation

from tigascoring.xp_scoring import compute_user_score_in_xp_v2, get_ranking_data, compute_user_score_in_xp_v2_fast
from rest_framework.exceptions import ParseError
from django.core.paginator import Paginator
import math
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch


@xframe_options_exempt
@cache_page(60 * 15)
def show_usage(request):
    real_tigausers = TigaUser.objects.filter(registration_time__gte=date(2014, 6, 13))
    real_reports = Report.objects.filter(Q(package_name='Tigatrapp', creation_time__gte=date(2014, 6, 24)) | Q(package_name='ceab.movelab.tigatrapp', package_version__gt=3))
    tz = get_localzone()
    ref_date = datetime.datetime(2014, 6, 13, 0, 0, 0,  tzinfo=tz)
    end_date = tz.localize(datetime.datetime.now())
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
        user_slug = request.query_params.get('user_slug', -1)
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
            pending = {'current_pending_n': current_pending.count(), 'current_pending': pending_detail, 'last_activity': 'Never'}
        return Response(pending)

@api_view(['GET'])
def workload_stats_per_user(request):
    if request.method == 'GET':
        user_slug = request.query_params.get('user_slug', -1)
        tz = get_localzone()
        queryset = User.objects.all()
        user = get_object_or_404(queryset, username=user_slug)
        single_user_work_output = []
        annotated_reports = ExpertReportAnnotation.objects.filter(user=user).filter(validation_complete=True)
        ref_date = datetime.datetime(2014, 1, 1, 0, 0, 0, tzinfo=tz)
        end_date = tz.localize(datetime.datetime.now())
        while ref_date <= end_date:
            single_user_work_output.append([time.mktime(ref_date.timetuple())*1000, annotated_reports.filter(last_modified__year=ref_date.year).filter(last_modified__month=ref_date.month).filter(last_modified__day=ref_date.day).count()])
            ref_date += timedelta(hours=24)
        return Response(single_user_work_output)


@api_view(['GET'])
def workload_daily_report_input(request):
    if request.method == 'GET':
        tz = get_localzone()
        daily_report_input = []
        ref_date = datetime.datetime(2014, 1, 1, 0, 0, 0, tzinfo=tz)
        end_date = tz.localize(datetime.datetime.now())
        reports = Report.objects.all()
        while ref_date <= end_date:
            daily_report_input.append([time.mktime(ref_date.timetuple())*1000,reports.filter(phone_upload_time__year=ref_date.year).filter(phone_upload_time__month=ref_date.month).filter(phone_upload_time__day=ref_date.day).count()])
            ref_date += timedelta(hours=24)
        return Response(daily_report_input)


def user_ids_string_to_int_array(user_ids_str):
    user_ids_str_array = user_ids_str.split(',')
    user_ids_int_array = []
    for id in user_ids_str_array:
        try:
            int_id = int(id)
            user_ids_int_array.append(int_id)
        except ValueError:
            user_ids_int_array = []
    return user_ids_int_array


@api_view(['GET'])
def workload_available_reports(request):
    if request.method == 'GET':
        user_id_filter = settings.USERS_IN_STATS
        user_ids_str = request.query_params.get('user_ids', None)
        if user_ids_str is not None:
            user_ids_arr = user_ids_string_to_int_array(user_ids_str)
            if len(user_ids_arr) > 0:
                user_id_filter = user_ids_arr
        current_pending = Report.objects.exclude(creation_time__year=2014).exclude(note__icontains="#345").exclude(hide=True).exclude(photos=None).filter(type='adult').annotate(n_annotations=Count('expert_report_annotations')).filter(n_annotations=0)
        current_progress = Report.objects.exclude(creation_time__year=2014).exclude(note__icontains="#345").exclude(hide=True).exclude(photos=None).filter(type='adult').annotate(n_annotations=Count('expert_report_annotations')).filter(n_annotations__lt=3).exclude(n_annotations=0)
        overall_pending = ExpertReportAnnotation.objects.filter(user__id__in=user_id_filter).filter(validation_complete=False).filter(report__type='adult')
        current_pending = filter_reports(current_pending)
        current_progress = filter_reports(current_progress)
        data = { 'current_pending_n' : len(current_pending), 'current_progress_n' : len(current_progress), 'overall_pending': overall_pending.count()}
        return Response(data)


def compute_speedmeter_params():
    current_date = timezone.now()
    date_7_days_ago = current_date - datetime.timedelta(days=7)
    reports_last_seven = Report.objects.filter(creation_time__gte=date_7_days_ago).filter(
        creation_time__lte=current_date)

    date_intervals = []
    days = 7
    while days >= 0:
        date_intervals.append(current_date - datetime.timedelta(days=days))
        days -= 1

    results = []
    for idx, val in enumerate(date_intervals):
        if idx + 1 >= len(date_intervals):
            break
        r = Report.objects.filter(creation_time__gte=date_intervals[idx]).filter(
            creation_time__lte=date_intervals[idx + 1])
        results.append(len(r))

    total = 0
    for result in results:
        total = total + result
    avg = total / len(results)

    data = {'reports_last_seven': len(reports_last_seven), 'avg_last_seven': avg}
    return data


@api_view(['GET'])
def speedmeter_api(request):
    if request.method == 'GET':
        data = compute_speedmeter_params()
        return Response(data)


def get_sunburst_data(days_back, categories):
    cursor = connection.cursor()
    sql = """
                select 
                distinct    
                version_uuid, 
                c.nom_ccaa,
                'c' || c.cod_ccaa,
                p.nomprov,
                'p' || p.codprov,
                municipality,
                'm' || mm.codigoine
                from 
                map_aux_reports m,
                municipis_4326 mm,
                provincies_4326 p,
                comunitats_4326 c
                where 
                m.municipality = mm.nombre
                AND m.private_webmap_layer in %s 
                AND mm.cod_ccaa = c.cod_ccaa
                AND mm.codprov = p.codprov
                AND observation_date >= (NOW() - interval '%s days')
                AND m.municipality is not null order by 3, 5, 7
            """

    cursor.execute(sql, (categories, days_back))
    data = cursor.fetchall()
    return json.dumps(data)


@login_required
def site_sunburst(request):
    data = get_sunburst_data(30, ('storm_drain_dry', 'storm_drain_water', 'breeding_site_other',) )

    context = {
        'data': data,
        'header': 'Sunburst graph of breeding sites in Spain last 30 days, by region',
        'call_to_action': 'Click the slices for drilldown!',
        'graph_title': 'Sampling by Regions, Spain',
        'categories' : ["*Breeding sites*: citizens' observations of possible breeding sites (storm drain or sewer and other categories of possible breeding sites) of tiger or yellow fever mosquitoes. It includes reports that contain at least one picture and that it has been evaluated by entomological experts, reports with at least one picture that have not been evaluated by experts and it might also contain reports without pictures."]
    }

    return render(request, 'stats/sunburst.html', context)


@login_required
def adult_sunburst(request):
    data = get_sunburst_data(30, ('mosquito_tiger_probable','mosquito_tiger_confirmed',) )

    context = {
        'data': data,
        'header': 'Sunburst graph of tiger mosquito observations in Spain last 30 days, by region',
        'call_to_action': 'Click the slices for drilldown!',
        'graph_title': 'Sampling by Regions, Spain',
        'categories' : ['*Confirmed or possible tiger mosquito*: it includes reports from citizen tagged by them as "adult mosquito", that contain at least one picture and that it has been evaluated by entomological experts. According to these experts, the picture/s of this observation could be tiger mosquito (Aedes albopictus). If their taxonomic features can be clearly seen, especially the white stripe on head and thorax, it is classified as "confirmed". If some features cannot be observed, it is classified as "possible".']
    }

    return render(request, 'stats/sunburst.html', context)


@login_required
def stats_directory(request):
    context = {}
    return render(request, 'stats/directory.html', context)


@xframe_options_exempt
def speedmeter(request):
    data = compute_speedmeter_params()
    context = {'data': data}
    return render(request, 'stats/speedmeter.html', context)


@login_required
def mosquito_ccaa_rich_iframetest_sites(request):
    context = {}
    return render(request, 'stats/mosquito_ccaa_rich_iframetest_sites.html', context)


@login_required
def mosquito_ccaa_rich_iframetest(request):
    context = {}
    return render(request, 'stats/mosquito_ccaa_rich_iframetest.html', context)


def oldActYear():
    cursor2 = connection.cursor()

    sql_template_years = """SELECT extract(year from observation_date) y 
                                FROM public.map_aux_reports
                                group by y
                            """

    cursor2.execute(sql_template_years)
    years = cursor2.fetchall()
    maxVal = int(max(years)[0])
    minVal = int(min(years)[0])
    yearsMaxMin = []
    yearsMaxMin.append({'max': maxVal, 'min': minVal})

    return yearsMaxMin


@login_required
@xframe_options_exempt
def mosquito_ccaa_rich(request, category='confirmed'):
    cursor = connection.cursor()
    sql_template = """
        select count("version_UUID"), extract(year from observation_date), nomprov, code_hc
        from 
        (
            (
            select *
            from
            map_aux_reports m,
            tigaserver_app_report r
            where private_webmap_layer in %s AND
            m.version_uuid = r."version_UUID") r
            join
            provincies_4326 p
            on st_contains(p.geom,r.point)
        ) as t 
        group by nomprov, extract(year from observation_date), code_hc order by 3, 2
    """

    t = oldActYear()

    categories = ()

    if category == 'confirmedpossible':

        categories = ('mosquito_tiger_confirmed', 'mosquito_tiger_probable',)
        #sql_template = sql_template.format('\'mosquito_tiger_confirmed\',\'mosquito_tiger_probable\'')

        title_linechart = 'Number of confirmed and possible mosquito tiger observations, ' + str(t[0]['min']) + '-' + str(t[0]['max']) + ''
        title = 'Confirmed and possible mosquito tiger observations, ' + str(t[0]['min']) + '-' + str(t[0]['max']) + ''
        series_title = 'Confirmed and possible mosquito tiger observations, ' + str(t[0]['min']) + '-' + str(t[0]['max']) + ''
        minColor = '#fef0d9'
        maxColor = '#b30000'

    elif category == 'confirmedpossibleunident':

        categories = ('mosquito_tiger_confirmed', 'mosquito_tiger_probable', 'unidentified')
        #sql_template = sql_template.format('\'mosquito_tiger_confirmed\',\'mosquito_tiger_probable\',\'unidentified\'')

        title_linechart = 'Number of confirmed, possible and unidentifiable mosquito tiger observations'
        title = 'Confirmed, possible and unidentifiable mosquito tiger observations, ' + str(t[0]['min']) + '-' + str(t[0]['max']) + ''
        series_title = 'Confirmed, possible and unidentifiable mosquito tiger observations, ' + str(t[0]['min']) + '-' + str(t[0]['max']) + ''

        minColor = '#fef0d9'
        maxColor = '#b30000'

    elif category == 'confirmed':

        categories = ('mosquito_tiger_confirmed',)
        #sql_template = sql_template.format('\'mosquito_tiger_confirmed\'')

        title_linechart = 'Number of confirmed mosquito tiger observations, ' + str(t[0]['min']) + '-' + str(t[0]['max']) + ''
        title = 'Confirmed mosquito tiger observations, ' + str(t[0]['min']) + '-' + str(t[0]['max']) + ''
        series_title = 'Confirmed mosquito tiger observations, ' + str(t[0]['min']) + '-' + str(t[0]['max']) + ''

        minColor = '#fef0d9'
        maxColor = '#b30000'

    elif category == 'probable':

        categories = ('mosquito_tiger_probable',)
        #sql_template = sql_template.format('\'mosquito_tiger_probable\'')

        title_linechart = 'Number of possible mosquito tiger observations, ' + str(t[0]['min']) + '-' + str(t[0]['max']) + ''
        title = 'Possible mosquito tiger observations, ' + str(t[0]['min']) + '-' + str(t[0]['max']) + ''
        series_title = 'Possible mosquito tiger observations, ' + str(t[0]['min']) + '-' + str(t[0]['max']) + ''

        minColor = '#fef0d9'
        maxColor = '#b30000'

    elif category == 'other':

        categories = ('other_species',)
        #sql_template = sql_template.format('\'other_species\'')

        title_linechart = 'Number of other species observations, ' + str(t[0]['min']) + '-' + str(t[0]['max']) + ''
        title = 'Other species observations, ' + str(t[0]['min']) + '-' + str(t[0]['max']) + ''
        series_title = 'Other species observations, ' + str(t[0]['min']) + '-' + str(t[0]['max']) + ''

        minColor = '#fef0d9'
        maxColor = '#b30000'

    elif category == 'unidentified':

        categories = ('unidentified',)
        #sql_template = sql_template.format('\'unidentified\'')

        title_linechart = 'Number of unidentifiable observations, ' + str(t[0]['min']) + '-' + str(t[0]['max']) + ''
        title = 'Unidentifiable observations, ' + str(t[0]['min']) + '-' + str(t[0]['max']) + ''
        series_title = 'Unidentifiable observations, ' + str(t[0]['min']) + '-' + str(t[0]['max']) + ''

        minColor = '#fef0d9'
        maxColor = '#b30000'

    elif category == 'all':

        categories = ('mosquito_tiger_confirmed', 'mosquito_tiger_probable', 'unidentified', 'other_species',)
        #sql_template = sql_template.format('\'unidentified\'')

        title_linechart = 'All categories, ' + str(t[0]['min']) + '-' + str(t[0]['max']) + ''
        title = 'All categories, ' + str(t[0]['min']) + '-' + str(t[0]['max']) + ''
        series_title = 'All categories, ' + str(t[0]['min']) + '-' + str(t[0]['max']) + ''

        minColor = '#fef0d9'
        maxColor = '#b30000'

    elif category == 'storm_drain_water':

        categories = ('storm_drain_water', )
        # sql_template = sql_template.format('\'unidentified\'')

        title_linechart = 'Breeding sites with water, ' + str(t[0]['min']) + '-' + str(t[0]['max']) + ''
        title = 'Breeding sites with water, ' + str(t[0]['min']) + '-' + str(t[0]['max']) + ''
        series_title = 'Breeding sites with water, ' + str(t[0]['min']) + '-' + str(t[0]['max']) + ''

        minColor = '#ece7f2'
        maxColor = '#2b8cbe'

    elif category == 'storm_drain_dry':

        categories = ('storm_drain_dry', )

        title_linechart = 'Breeding sites without water, ' + str(t[0]['min']) + '-' + str(t[0]['max']) + ''
        title = 'Breeding sites without water, ' + str(t[0]['min']) + '-' + str(t[0]['max']) + ''
        series_title = 'Breeding sites without water, ' + str(t[0]['min']) + '-' + str(t[0]['max']) + ''

        minColor = '#ece7f2'
        maxColor = '#2b8cbe'

    elif category == 'storm_drain':

        categories = ('storm_drain_dry', 'storm_drain_water',)

        title_linechart = 'Breeding sites with and without water, ' + str(t[0]['min']) + '-' + str(t[0]['max']) + ''
        title = 'Breeding sites with and without water, ' + str(t[0]['min']) + '-' + str(t[0]['max']) + ''
        series_title = 'Breeding sites with and without water, ' + str(t[0]['min']) + '-' + str(t[0]['max']) + ''

        minColor = '#ece7f2'
        maxColor = '#2b8cbe'

    elif category == 'breeding_site_other':

        categories = ('breeding_site_other', )

        title_linechart = 'Other breeding sites, ' + str(t[0]['min']) + '-' + str(t[0]['max']) + ''
        title = 'Other breeding sites, ' + str(t[0]['min']) + '-' + str(t[0]['max']) + ''
        series_title = 'Other breeding sites, ' + str(t[0]['min']) + '-' + str(t[0]['max']) + ''

        minColor = '#ece7f2'
        maxColor = '#2b8cbe'

    elif category == 'all_sites':

        categories = ('storm_drain_dry','storm_drain_water','breeding_site_other',)

        title_linechart = 'All breeding sites, ' + str(t[0]['min']) + '-' + str(t[0]['max']) + ''
        title = 'All breeding sites, ' + str(t[0]['min']) + '-' + str(t[0]['max']) + ''
        series_title = 'All breeding sites, ' + str(t[0]['min']) + '-' + str(t[0]['max']) + ''

        minColor = '#ece7f2'
        maxColor = '#2b8cbe'

    else:

        categories = ('mosquito_tiger_confirmed',)
        #sql_template = sql_template.format('\'mosquito_tiger_confirmed\'')

        title_linechart = ''
        title = ''
        series_title = ''

        minColor = '#fef0d9'
        maxColor = '#b30000'

    cursor.execute(sql_template,(categories,))
    map_data = cursor.fetchall()

    now = datetime.datetime.now()
    current_year = now.year
    years = []

    for i in range(2014, current_year + 1):
        years.append(i)



    context = {
        'map_data': json.dumps(map_data),
        'years': json.dumps(years),
        'title_linechart': title_linechart,
        'title': title,
        'series_title': series_title,
        'minColor': minColor,
        'maxColor': maxColor
    }
    return render(request, 'stats/mosquito_ccaa_rich.html', context)

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

    '''    
    **** alt query. Does exactly the same as the one below, but the data is separated by adult category ****
    '''

    cursor.execute("""
        select count("version_UUID"), extract(year from server_upload_time), extract(month from server_upload_time), private_webmap_layer
        from 
        (
        select 
        r."version_UUID",
        r.server_upload_time,
        m.private_webmap_layer
        from 
        tigaserver_app_report r,
        (select version_uuid,private_webmap_layer from map_aux_reports where private_webmap_layer in ('mosquito_tiger_confirmed','mosquito_tiger_probable', 'other_species','unidentified','storm_drain_dry','storm_drain_water','breeding_site_other')) m
        where r."version_UUID" = m.version_uuid
        ) as t1
        group by extract(year from server_upload_time), extract(month from server_upload_time), private_webmap_layer
        order by 2,3
    """)
    all_sliced = cursor.fetchall()


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

    context = {'adults': json.dumps(adults), 'sites': json.dumps(sites), 'years': json.dumps(years), 'years_list': years, 'all_sliced': json.dumps(all_sliced)}
    return render(request, 'stats/user_activity.html', context)


def create_pie_data(request, categories, view_name):
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
                where private_webmap_layer in %s AND
                m.version_uuid = r."version_UUID") r
                join
                provincies_4326 p
                on st_contains(p.geom,r.point)
            ) as t 
            group by nomprov, code_hc, private_webmap_layer order by 2, 4
        """, (categories,))
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
                where private_webmap_layer in %s AND
                m.version_uuid = r."version_UUID") r
                join
                provincies_4326 p
                on st_contains(p.geom,r.point)
            ) as t 
            group by nomprov, extract(year from observation_date), code_hc, private_webmap_layer order by 2, 3
        """, (categories,))
    map_data_year = cursor.fetchall()

    now = datetime.datetime.now()
    current_year = now.year
    years = []

    for i in range(2014, current_year + 1):
        years.append(i)

    context = {'map_data': json.dumps(map_data), 'map_data_year': json.dumps(map_data_year), 'years': json.dumps(years)}
    return render(request, view_name, context)

@login_required
def report_stats_ccaa_pie_sites(request):
    categories = ('storm_drain_water', 'storm_drain_dry', 'breeding_site_other', )
    return create_pie_data(request, categories, 'stats/report_stats_ccaa_pie_sites.html')

@login_required
def report_stats_ccaa_pie(request):
    categories = ('mosquito_tiger_confirmed', 'mosquito_tiger_probable', 'other_species', 'unidentified',)
    return create_pie_data(request, categories, 'stats/report_stats_ccaa_pie.html')


def stats_user_score(request, user_uuid=None):
    user_score = compute_user_score_in_xp_v2(user_uuid,update=True)
    context = { "score_data": user_score }
    return render(request, 'stats/user_score.html', context)


def get_index_of_uuid(objects, user_uuid):
    index = 0
    for user in objects:
        if user['user_uuid'] == user_uuid:
            break
        index += 1
    return index

def get_page_of_index(index, page_size):
    index_base_1 = index + 1
    return int(math.ceil( float(index_base_1) / float(page_size) ))

def stats_user_ranking(request, page=1, user_uuid=None):
    current_locale = request.LANGUAGE_CODE
    user_has_score = False
    try:
        info_url = reverse('scoring_' + current_locale)
    except NoReverseMatch:
        info_url = reverse('scoring_en')
    user = None
    if user_uuid is not None:
        try:
            user = TigaUser.objects.get(pk=user_uuid)
            user.get_identicon()
            user_score = compute_user_score_in_xp_v2(user_uuid, update=True)
            if user_score['total_score'] > 0:
                user_has_score = True

        except TigaUser.DoesNotExist:
            pass
    seek = request.GET.get('seek', 'f')
    ranking = get_ranking_data()
    objects = ranking['data']
    page_length = 5
    p = Paginator(objects, page_length )
    if seek == 't':
        index = get_index_of_uuid(objects,user_uuid)
        page_of_index = get_page_of_index(index, page_length)
        current_page = p.page(int(page_of_index))
        return HttpResponseRedirect(reverse('stats_user_ranking', args=[int(page_of_index),user_uuid]))
    else:
        current_page = p.page(int(page))
        previous = None
        nextp = None
        if current_page.has_previous():
            previous = current_page.previous_page_number()
        if current_page.has_next():
            nextp = current_page.next_page_number()
        objects = current_page.object_list
        context = {
                    'data': objects,
                    'user_has_score': user_has_score,
                    'pagination':
                        {
                            'page': int(page),
                              'total': p.num_pages,
                              'start': current_page.start_index(),
                              'end': current_page.end_index(),
                              'total': p.count,
                              'previous': previous,
                              'next': nextp,
                              'first': 1,
                              'last': p.num_pages
                        }
                  }
        if user is not None:
            context['user_id'] = user_uuid
        context['info_url'] = info_url
        return render(request, 'stats/user_ranking.html', context)

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

    years = set()
    for elem in data:
        years.add(int(elem[1]))
    years = list(years)
    years.sort()


    # context = {'data': json.dumps(data), 'data_ccaa': json.dumps(data_ccaa),  'm_data': json.dumps(m_data), 'years': years}
    context = {'data': json.dumps(data), 'data_ccaa': json.dumps(data_ccaa), 'years': years}
    return render(request, 'stats/report_stats_ccaa.html', context)


@login_required
def global_assignments(request):
    this_user = request.user
    this_user_is_superexpert = this_user.groups.filter(name='superexpert').exists()
    if this_user_is_superexpert:
        national_supervisors = User.objects.filter(userstat__isnull=False).filter(userstat__national_supervisor_of__isnull=False).order_by('userstat__national_supervisor_of__name_engl').all()
        keys = Report.objects.exclude(creation_time__year=2014).filter(type='adult').values('report_id').annotate(Max('version_number')).annotate(Min('version_number')).annotate(Count('version_number'))
        report_id_table = {}
        for row in keys:
            report_id_table[row['report_id']] = {'max_version': row['version_number__max'],
                                                 'min_version': row['version_number__min'],
                                                 'num_versions': row['version_number__count']}
        data = []
        total_unassigned = 0
        total_progress = 0
        total_pending = 0
        # manually add spain
        current_country = 17
        unassigned = Report.objects.exclude(creation_time__year=2014).exclude(note__icontains="#345").exclude(
            hide=True).exclude(photos=None).filter(type='adult').filter(
            Q(country_id=current_country) | Q(country_id__isnull=True)).annotate(
            n_annotations=Count('expert_report_annotations')).filter(n_annotations=0)
        unassigned_filtered = filter(lambda x: report_id_table[x.report_id]['num_versions'] == 1 or (
                    report_id_table[x.report_id]['min_version'] != -1 and x.version_number ==
                    report_id_table[x.report_id]['max_version']), unassigned)
        progress = Report.objects.exclude(creation_time__year=2014).exclude(note__icontains="#345").exclude(
            hide=True).exclude(photos=None).filter(type='adult').filter(
            Q(country_id=current_country) | Q(country_id__isnull=True)).annotate(
            n_annotations=Count('expert_report_annotations')).filter(n_annotations__lt=3).exclude(n_annotations=0)
        progress_filtered = filter(lambda x: report_id_table[x.report_id]['num_versions'] == 1 or (
                    report_id_table[x.report_id]['min_version'] != -1 and x.version_number ==
                    report_id_table[x.report_id]['max_version']), progress)
        user_id_filter = settings.USERS_IN_STATS
        pending = ExpertReportAnnotation.objects.filter(user__id__in=user_id_filter).filter(
            validation_complete=False).filter(report__type='adult').values('report')
        n_unassigned = len(list(unassigned_filtered))
        n_progress = len(list(progress_filtered))
        n_pending = pending.count()
        data.append(
            {
                "ns_id": 'N/A',
                "ns_username": 'N/A',
                "ns_country_id": 17,
                "ns_country_code": 'ESP',
                "ns_country_name": 'Spain',
                "unassigned": n_unassigned,
                "progress": n_progress,
                "pending": n_pending
            }
        )
        total_unassigned += n_unassigned
        total_progress += n_progress
        total_pending += n_pending
        for user in national_supervisors:
            current_country = user.userstat.national_supervisor_of.gid
            unassigned = Report.objects.exclude(creation_time__year=2014).exclude(note__icontains="#345").exclude(hide=True).exclude(photos=None).filter(type='adult').filter(country_id=current_country).annotate(n_annotations=Count('expert_report_annotations')).filter(n_annotations=0)
            unassigned_filtered = filter( lambda x: report_id_table[x.report_id]['num_versions'] == 1 or (report_id_table[x.report_id]['min_version'] != -1 and x.version_number == report_id_table[x.report_id]['max_version']), unassigned )
            progress = Report.objects.exclude(creation_time__year=2014).exclude(note__icontains="#345").exclude(hide=True).exclude(photos=None).filter(type='adult').filter(country_id=current_country).annotate(n_annotations=Count('expert_report_annotations')).filter(n_annotations__lt=3).exclude(n_annotations=0)
            progress_filtered = filter( lambda x: report_id_table[x.report_id]['num_versions'] == 1 or (report_id_table[x.report_id]['min_version'] != -1 and x.version_number == report_id_table[x.report_id]['max_version']), progress )
            user_id_filter = UserStat.objects.filter(native_of__gid=current_country).values('user__id')
            pending = ExpertReportAnnotation.objects.filter(user__id__in=user_id_filter).filter(validation_complete=False).filter(report__type='adult').values('report')
            n_unassigned = len(list(unassigned_filtered))
            n_progress = len(list(progress_filtered))
            n_pending = pending.count()
            data.append(
                {
                    "ns_id":user.id,
                    "ns_username":user.username,
                    "ns_country_id":user.userstat.national_supervisor_of.gid,
                    "ns_country_code": user.userstat.national_supervisor_of.iso3_code,
                    "ns_country_name":user.userstat.national_supervisor_of.name_engl,
                    "unassigned": n_unassigned,
                    "progress": n_progress,
                    "pending": n_pending
                }
            )
            total_unassigned += n_unassigned
            total_progress += n_progress
            total_pending += n_pending
        summary = { 'total_unassigned':total_unassigned, 'total_progress':total_progress, 'total_pending':total_pending }
        context = {'data': data, 'encoded_data': json.dumps(data), 'summary': summary}
        return render(request, 'stats/global_assignments.html', context)
    else:
        return HttpResponse("You need to be logged in as superexpert to view this page. If you have have been recruited as an expert and have lost your log-in credentials, please contact MoveLab.")


@login_required
def workload_stats(request, country_id=None):
    this_user = request.user
    user_id_filter = settings.USERS_IN_STATS
    this_user_is_superexpert = this_user.groups.filter(name='superexpert').exists()
    if this_user_is_superexpert:
        if country_id is None:
            users = User.objects.filter(groups__name='expert').filter(id__in=user_id_filter).order_by('first_name','last_name')
            context = {'users': users, 'load_everything_on_start': True, 'country_name': 'Spain'}
            return render(request, 'stats/workload.html', context)
        else:
            user_id_filter = UserStat.objects.filter(native_of__iso3_code=country_id).values('user__id')
            country_name = 'Unknown country??'
            try:
                country_name = EuropeCountry.objects.get(iso3_code=country_id).name_engl
            except:
                pass
            users = User.objects.filter(groups__name='expert').filter(id__in=user_id_filter).order_by('first_name', 'last_name')
            context = {'users': users, 'load_everything_on_start': True, 'country_name': country_name}
            return render(request, 'stats/workload.html', context)
    else:
        return HttpResponse("You need to be logged in as superexpert to view this page. If you have have been recruited as an expert and have lost your log-in credentials, please contact MoveLab.")


def show_fix_users(request):
    real_fixes = Fix.objects.filter(fix_time__gt='2014-06-13')
    tz = get_localzone()
    ref_date = datetime.datetime(2014, 6, 13, 0, 0, 0,  tzinfo=tz)
    end_date = tz.localize(datetime.datetime.now())
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
    ref_date = datetime.datetime(2014, 6, 13,  tzinfo=tz)
    end_date = tz.localize(datetime.datetime.now())
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


@login_required
def hashtag_map(request):
    context = {}
    return render(request, 'stats/hashtag_map.html', context)


@api_view(['GET'])
@permission_classes([])
def get_user_xp_data(request):
    user_id = request.query_params.get('user_id', '-1')
    locale = request.query_params.get('locale', 'en')
    update = request.query_params.get('update', False)
    u = None
    try:
        u = TigaUser.objects.get(pk=user_id)
    except TigaUser.DoesNotExist:
        raise ParseError(detail='user does not exist')

    #language = translation.get_language_from_request(request)
    translation.activate(locale)

    if update == False:
        retval = { "total_score": u.score_v2 }
    else:
        retval = compute_user_score_in_xp_v2(user_id, True)
    return Response(retval)


@api_view(['GET'])
def get_hashtag_map_data(request):
    hashtag = request.query_params.get('ht', '')
    data = []
    if hashtag.strip() == '':
        return Response({ 'stats': '', 'data': data})
    else:
        # - data summary
        # earliest data
        # latest data
        # number of points
        dates = []
        r = Report.objects.filter(note__icontains=hashtag).order_by('-server_upload_time')[:200]
        n = 0
        for report in r:
            if report.latest_version:
                n = n + 1
                dates.append(report.server_upload_time)
                data.append({ 'note': report.note, 'picture': report.get_photo_html(), 'lat': report.get_lat(), 'lon': report.get_lon(), 'date_uploaded': report.server_upload_time.strftime('%d-%m-%Y / %H:%M:%S') })
    min_date_str = ''
    max_date_str = ''
    if len(dates) == 0:
        min_date_str = 'N/A'
        max_date_str = 'N/A'
    else:
        min_date = min(dates)
        min_date_str = min_date.strftime('%d-%m-%Y / %H:%M:%S')
        max_date = max(dates)
        max_date_str = max_date.strftime('%d-%m-%Y / %H:%M:%S')
    return Response({ 'stats':{ 'earliest_date': min_date_str, 'latest_date': max_date_str, 'n': n }, 'data': data})


@login_required
def expert_report_assigned_data(request):

    report_list = []

    a = ExpertReportAnnotation.objects.all().order_by('-created')

    paginator = Paginator(a, 50)
    page = request.GET.get('page', 1)
    try:
        reports = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        reports = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        reports = paginator.page(paginator.num_pages)


    for t in reports:
        if t.report.country is None:
            report_list.append({
                'assignedExpert': str(t.user),
                'codiReport': str(t.report),
                'ubication': 'Null',
                'assignationDate': t.created.strftime("%Y-%m-%d")
            })
        else:
            report_list.append({
                'assignedExpert': str(t.user),
                'codiReport': str(t.report),
                'ubication': str(t.report.country.name_engl),
                'assignationDate': t.created.strftime("%Y-%m-%d")
            })
    pages = range(1, reports.paginator.num_pages + 1)

    return render(request, 'tigacrafting/expert_report_assigned_data.html', {'list': report_list, 'pages': pages, 'reports': reports})