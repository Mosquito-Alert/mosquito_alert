from django.shortcuts import render

from tigaserver_app.models import *
from tigacrafting.models import UserStat
from django.views.decorators.clickjacking import xframe_options_exempt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view,permission_classes
from rest_framework.response import Response
from tigaserver_project import settings
import json
from rest_framework.exceptions import ParseError
from django.core.paginator import Paginator
import math
from django.utils import translation

from rest_framework.exceptions import ParseError
from django.core.paginator import Paginator
import math
from django.urls import reverse
from django.db.models import Count
from django.db.models.functions import Extract, Trunc


@xframe_options_exempt
# @cache_page(60 * 15)
def show_usage(request):
    def get_cumsum(qs, datetime_fieldname: str, trunc_by: str) -> dict:
        qs = qs.annotate(
            week_epoch=Extract(
                Trunc(datetime_fieldname, kind=trunc_by),
                'epoch'
            )
        ).values('week_epoch').annotate(
            n=Count(1)
        ).order_by('week_epoch')

        cumsum = 0
        result = []
        for obj in qs.iterator():
            cumsum += obj['n']
            result.append({
                'date': obj['week_epoch'],
                'n': cumsum
            })
        return result

    context = {
        'users': get_cumsum(
            qs= TigaUser.objects,
            datetime_fieldname='registration_time',
            trunc_by='week'
        ),
        'site_reports': get_cumsum(
            qs=Report.objects.filter(type=Report.TYPE_SITE),
            datetime_fieldname='server_upload_time',
            trunc_by='week'
        ),
        'adult_reports': get_cumsum(
            qs=Report.objects.filter(type=Report.TYPE_ADULT),
            datetime_fieldname='server_upload_time',
            trunc_by='week'
        )
    }
    return render(request, 'stats/chart.html', context)

@api_view(['GET'])
def workload_pending_per_user(request):
    if request.method == 'GET':
        user_slug = request.query_params.get('user_slug', -1)
        user = get_object_or_404(User, username=user_slug)

        if not hasattr(user, 'userstat'):
            return

        pending_detail = []
        for ano in user.userstat.pending_annotations.select_related('report').iterator():
            pending_detail.append(
                {
                    'report_id': ano.report_id, 
                    'created': ano.report.creation_time.strftime('%d/%m/%Y - %H:%M:%S')
                }
            )

        last_activity = user.userstat.completed_annotations.order_by('last_modified').last()

        pending = {
            'current_pending_n': user.userstat.num_pending_annotations,
            'current_pending': pending_detail,
            'last_activity': last_activity.last_modified.strftime('%d/%m/%Y') if last_activity else 'Never'
        }
        return Response(pending)

@api_view(['GET'])
def workload_stats_per_user(request):
    if request.method == 'GET':
        user_slug = request.query_params.get('user_slug', -1)
        user = get_object_or_404(User, username=user_slug)

        if not hasattr(user, 'userstat'):
            return

        qs = user.userstat.completed_annotations.annotate(
            week_epoch=Trunc('last_modified', kind='week')
        ).values('week_epoch').annotate(
            n=Count(1)
        ).order_by('week_epoch')

        # NOTE: convert to miliseconds (epoch)
        return Response([(r['week_epoch'].timestamp()*1000, r['n']) for r in qs.iterator()])


@api_view(['GET'])
def workload_daily_report_input(request):
    if request.method == 'GET':

        qs = Report.objects.annotate(
            day_epoch=Trunc('server_upload_time', kind='day')
        ).values('day_epoch').annotate(
            n=Count(1)
        ).order_by('day_epoch')

        # NOTE: convert to miliseconds (epoch)
        return Response([(r['day_epoch'].timestamp()*1000, r['n']) for r in qs.iterator()])


@api_view(['GET'])
def workload_available_reports(request):
    if request.method == 'GET':
        user_id_filter = settings.USERS_IN_STATS
        user_ids_str = request.query_params.get('user_ids', None)
        if user_ids_str is not None:
            try:
                user_ids_arr = [int(x) for x in user_ids_str.split(',')]
            except ValueError:
                user_ids_arr = []
            if len(user_ids_arr) > 0:
                user_id_filter = user_ids_arr
        current_pending = IdentificationTask.objects.new()
        current_progress = IdentificationTask.objects.ongoing()

        overall_pending = ExpertReportAnnotation.objects.filter(
            user__pk__in=user_id_filter,
            identification_task__isnull=False
        ).completed(False)

        data = { 'current_pending_n' : current_pending.count(), 'current_progress_n' : current_progress.count(), 'overall_pending': overall_pending.count()}
        return Response(data)


def stats_user_score(request, user_uuid=None):
    if user_uuid is not None:
        try:
            user = TigaUser.objects.get(pk=user_uuid)
            user.get_identicon()
        except TigaUser.DoesNotExist:
            pass

    if user.score_v2_struct is None:
        user.update_score(commit=True)
    context = { "score_data": user.score_v2_struct, "score_last_update": user.last_score_update }
    return render(request, 'stats/user_score.html', context)


def get_index_of_uuid(objects, user_uuid):
    index = 0
    position = -1
    for user in objects:
        if user.user_uuid == user_uuid:
            position = index
            break
        index += 1
    return position


def get_page_of_index(index, page_size):
    index_base_1 = index + 1
    return int(math.ceil( float(index_base_1) / float(page_size) ))


def stats_user_ranking(request, page=1, user_uuid=None):
    current_locale = getattr(request, "LANGUAGE_CODE", "en")
    info_url = f'https://app.mosquitoalert.com/{current_locale}/info/score'
    user_has_score = False
    user = None
    if user_uuid is not None:
        try:
            user = TigaUser.objects.get(pk=user_uuid)
            user.get_identicon()

            if user.score_v2_struct is None:
                user.update_score(commit=True)
            user_score = user.score_v2_struct
            user_has_score = bool(user.score_v2)
        except TigaUser.DoesNotExist:
            pass
    seek = request.GET.get('seek', 'f')

    objects = RankingData.objects.all().order_by('-score_v2')
    last_update = objects.first().last_update
    page_length = 5
    p = Paginator(objects, page_length )
    if seek == 't':
        index = get_index_of_uuid(objects,user_uuid)
        if index == -1:
            page_of_index = 1
        else:
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
                    'last_update': last_update,
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
        if user_uuid is not None:
            context['user_id'] = user_uuid
        if user is not None:
            context['user'] = user
        context['info_url'] = info_url
        return render(request, 'stats/user_ranking.html', context)


@login_required
def global_assignments(request):
    this_user = request.user

    is_national_supervisor = this_user.userstat.is_national_supervisor()
    is_super_expert = this_user.userstat.is_superexpert()

    if not (is_national_supervisor or is_super_expert):
        return HttpResponse("You need to be logged in as superexpert or be a national supervisor to view this page. If you have have been recruited as an expert and have lost your log-in credentials, please contact MoveLab.")

    task_qs = IdentificationTask.objects
    if is_national_supervisor:
        # Only allow stats from its country
        task_qs = task_qs.filter(report__country=this_user.userstat.national_supervisor_of)

    n_unassigned = task_qs.new().in_exclusivity_period(False).annotate(
        country=models.F('report__country')
    ).values('country').annotate(
        total_count=models.Count(1)
    ).values('country','total_count')

    n_in_exclusivity_period = task_qs.in_exclusivity_period().annotate(
        country=models.F('report__country')
    ).values('country').annotate(
        total_count=models.Count(1)
    ).values('country','total_count')

    n_progress = task_qs.ongoing().annotate(
        country=models.F('report__country')
    ).values('country').annotate(
        total_count=models.Count(1)
    ).values('country','total_count')

    n_pending = task_qs.annotating().annotate(
        country=models.F('report__country')
    ).values('country').annotate(
        total_count=models.Count(1)
    ).values('country','total_count')

    n_blocked = task_qs.blocked().annotate(
        country=models.F('report__country')
    ).values('country').annotate(
        total_count=models.Count(1)
    ).values('country','total_count')

    # Create a dictionary to store merged data
    stats_country_data = {}

    # Merge data from each list of dicts
    for data_list, fieldname in [(n_unassigned, "unassigned"), (n_progress, "progress"), (n_pending, "pending"), (n_blocked, "blocked"), (n_in_exclusivity_period, "reserved")]:
        for entry in data_list:
            country = entry['country'] or 'N/A'
            if country not in stats_country_data:
                stats_country_data[country] = {}
            stats_country_data[country][fieldname] = entry['total_count']

    country_info = list(EuropeCountry.objects.values('gid', 'iso3_code', 'name_engl', 'supervisors__user', 'supervisors__user__username'))

    # Append case when country is None
    country_info.append({'gid': 'N/A', 'iso3_code': 'Other', 'name_engl': 'Other', 'supervisors__user': None, 'supervisors__user__username': None})

    data = []
    for country in country_info:
        stats = stats_country_data.get(country['gid'])
        data.append(
            {
                "ns_id": country['supervisors__user'],
                "ns_username": country['supervisors__user__username'],
                "ns_country_id":country['gid'],
                "ns_country_code": country['iso3_code'],
                "ns_country_name":country['name_engl'],
                "unassigned": stats.get('unassigned', 0) if stats else 0,
                "progress": stats.get('progress', 0) if stats else 0,
                "pending": stats.get('pending', 0) if stats else 0,
                "blocked": stats.get('blocked', 0) if stats else 0,
                "reserved": stats.get('reserved', 0) if stats else 0,
            }
        )

    summary = {
        'total_unassigned': sum(item['unassigned'] for item in data),
        'total_progress': sum(item['progress'] for item in data),
        'total_pending': sum(item['pending'] for item in data),
        'total_blocked': sum(item['blocked'] for item in data),
        'total_reserved': sum(item['reserved'] for item in data)
    }
    context = {'data': data, 'encoded_data': json.dumps(data), 'summary': summary, 'days': settings.ENTOLAB_LOCK_PERIOD}
    return render(request, 'stats/global_assignments.html', context)

@login_required
def global_assignments_list(request, country_code=None, status=None):
    if country_code == 'Other':
        country = None
        countryName = 'Others'
    else:
        country = get_object_or_404(EuropeCountry, iso3_code=country_code)
        countryName = country.name_engl

    qs = IdentificationTask.objects.filter(report__country=country)

    if status == 'pending':
        qs = qs.annotating()
        title = 'Pending'
    elif status == 'unassigned':
        qs = qs.new().in_exclusivity_period(False)
        title = 'Unassigned'
    elif status == 'progress':
        qs = qs.ongoing()
        title = 'In progress'
    elif status == 'reserved':
        qs = qs.in_exclusivity_period()
        title = 'Reserved for national supervisors'
    else:
        return HttpResponseBadRequest('status not found.')

    result = []
    # NOTE: chunk_size is needed in iterator when using prefetch_related since django 4.1
    for obj in qs.order_by('-created_at').prefetch_related('expert_report_annotations').iterator(chunk_size=1000):
        names = []
        for annotation in obj.expert_report_annotations.all():
            names.append(
                annotation.user.get_full_name() or annotation.user.username
            )

        expNamesJoined = ' / '.join(names)
        result.append(
            {
                'idReports': obj.report_id,
                'experts': expNamesJoined,
            }
        )

    context = {'data': result, 'country': country_code, 'status': status, 'countryName': countryName, 'reportStatus': title}

    return render(request, 'stats/global_assignments_list.html', context)




@login_required
def workload_stats(request, country_id=None):
    this_user = request.user
    user_id_filter = settings.USERS_IN_STATS
    if this_user.userstat and this_user.userstat.is_superexpert():
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


@api_view(['GET'])
@permission_classes([])
def get_user_xp_data(request):
    user_id = request.query_params.get('user_id', '-1')
    locale = request.query_params.get('locale', 'en')
    update = request.query_params.get('update', True)
    u = None
    try:
        u = TigaUser.objects.get(pk=user_id)
    except TigaUser.DoesNotExist:
        raise ParseError(detail='user does not exist')

    #language = translation.get_language_from_request(request)
    translation.activate(locale)

    if u.score_v2_struct is None:
        u.update_score(commit=True)

    retval = u.score_v2_struct
    retval['last_update'] = u.last_score_update

    return Response(retval)