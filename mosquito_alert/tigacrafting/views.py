# coding=utf-8
from django.shortcuts import render, get_object_or_404
import json

from rest_framework.decorators import api_view

from mosquito_alert.tigacrafting.models import *
from django.db.models import Count
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect
from django.urls import reverse
from django.conf import settings
from django.http import HttpResponse
from mosquito_alert.tigaserver_app.models import Notification, EuropeCountry, SentNotification, NotificationTopic, TOPIC_GROUPS, AcknowledgedNotification, UserSubscription
from django.db.models import Q
from django.contrib.auth.models import User, Group
from mosquito_alert.tigaserver_app.serializers import DataTableNotificationSerializer, DataTableAimalertSerializer
from django.db import transaction
import logging
from django.utils.translation import gettext as _
from mosquito_alert.tigacrafting.querystring_parser import parser
import functools
import operator

from decimal import *
from rest_framework.response import Response
from django.utils import timezone

#-----------------------------------#

logger_notification = logging.getLogger('mosquitoalert.notification')


@login_required
def report_expiration(request, country_id=None):
    this_user = request.user

    if not this_user.userstat.is_superexpert():
        return HttpResponse("You need to be logged in as superexpert to view this page. If you have have been recruited as an expert and have lost your log-in credentials, please contact MoveLab.")

    qs = ExpertReportAnnotation.objects.blocking()

    country = None
    if country_id is not None:
        country = get_object_or_404(EuropeCountry, pk=country_id)
        qs = qs.filter(identification_task__report__country=country)

    data_dict = {}
    for annotation in qs.select_related('user'):
        if annotation.user.username not in data_dict:
            data_dict[annotation.user.username] = []

        data_dict[annotation.user.username].append(
            {
                'report_uuid': annotation.identification_task.report_id,
                'days': (timezone.now() - annotation.created).days
            }
        )

    sorted_data = sorted(data_dict.items(), key=lambda x: x[1][0]['days'], reverse=True)

    return render(request, 'tigacrafting/report_expiration.html', { 'data':sorted_data, 'lock_period': settings.ENTOLAB_LOCK_PERIOD , 'country': country})


@transaction.atomic
@login_required
def expert_report_annotation(request):
    this_user = request.user

    if settings.SHOW_USER_AGREEMENT_ENTOLAB:
        if not this_user.userstat:
            return HttpResponse("There is a problem with your current user. Please contact the EntoLab admin at " + settings.ENTOLAB_ADMIN)

    this_user_is_expert = this_user.userstat.is_expert()
    this_user_is_superexpert = this_user.userstat.is_superexpert()

    if not (this_user_is_expert or this_user_is_superexpert):
        return HttpResponse("You need to be logged in as an expert member to view this page. If you have have been recruited as an expert and have lost your log-in credentials, please contact MoveLab.")

    if not this_user_is_superexpert:
        return HttpResponsePermanentRedirect('https://app.mosquitoalert.com')
    # NOTE: from now on, only superexpert is allowed to visit this view

    if request.method == 'GET':
        return render(request, 'tigacrafting/superexpert_report_annotation.html')


@login_required
def expert_status(request):
    this_user = request.user
    if this_user.groups.filter(Q(name='superexpert') | Q(name='movelab')).exists():
        groups = Group.objects.filter(name__in=['expert', 'superexpert'])
        return render(request, 'tigacrafting/expert_status.html', {'groups': groups})
    else:
        return HttpResponseRedirect(reverse('login'))

# var is an ExpertReportAnnotation
def reportannotation_formatter(var: ExpertReportAnnotation):
    return {
        'report_id': var.identification_task.report.version_UUID,
        'report_type': var.identification_task.report.type,
        'givenToExpert': var.created.strftime("%d/%m/%Y - %H:%M:%S"),
        'lastModified': var.last_modified.strftime("%d/%m/%Y - %H:%M:%S"),
        'draftStatus': ExpertReportAnnotation.Status(var.status).label,
        'getCategory': var.taxon.name if var.taxon else None,
    }


@api_view(['GET'])
def expert_report_pending(request):
    user = request.query_params.get('u', None)
    u = User.objects.get(username=user)
    x = ExpertReportAnnotation.objects.filter(user=u, is_finished=False)

    reports = []
    for var in x.select_related('identification_task', 'identification_task__report'):
        reports.append(reportannotation_formatter(var))

    context = {'pendingReports': reports}

    return Response(context)


@api_view(['GET'])
def expert_report_complete(request):
    user = request.query_params.get('u', None)
    u = User.objects.get(username=user)
    x = ExpertReportAnnotation.objects.filter(user=u, is_finished=True)

    reports = []
    for var in x.select_related('identification_task', 'identification_task__report'):
        reports.append(reportannotation_formatter(var))

    context = {'completeReports': reports}

    return Response(context)


@login_required
def coarse_filter(request):
    this_user = request.user
    if this_user.groups.filter(name='coarse_filter').exists():
        range_list = [n for n in range(10, 101, 10)]
        context = {
            'tasks_per_page_choices': range_list + [200, 300],
            'countries': EuropeCountry.objects.all().order_by('name_engl')
        }
        return render(request, 'tigacrafting/coarse_filter.html', context)
    else:
        return HttpResponse("You need to belong to the coarse filter group to access this page, please contact MoveLab.")

@login_required
def aimalog(request):
    return render(request, 'tigacrafting/aimalog.html',{})

@login_required
def notifications_version_two(request,user_uuid=None):
    this_user = request.user
    this_user_is_notifier = this_user.groups.filter(name='expert_notifier').exists()
    if this_user_is_notifier:
        user_uuid = request.GET.get('user_uuid',None)
        #total_users = TigaUser.objects.exclude(device_token='').filter(device_token__isnull=False).count()
        # TOPIC_GROUPS = ((0, 'General'), (1, 'Language topics'), (2, 'Country topics'))
        languages = []
        sorted_langs = sorted(settings.LANGUAGES, key=lambda tup: tup[1])
        for lang in sorted_langs:
            languages.append({'code':lang[0],'name':str(lang[1])})
        all_topics = []
        for group in TOPIC_GROUPS:
            if group[0] != 5: # exclude special topics i.e. global
                current_topics = []
                for topic in NotificationTopic.objects.filter(topic_group=group[0]).order_by('topic_description'):
                    current_topics.append({ 'topic_text': topic.topic_description, 'topic_value': topic.topic_code})
                topic_info = {
                    'topic_group_text': group[1],
                    'topic_group_value': group[0],
                    'topics': current_topics
                }
                all_topics.append(topic_info)
            else:
                pass
        return render(request, 'tigacrafting/notifications_version_two.html',{'user_id':this_user.id, 'user_uuid':user_uuid, 'topics_info': json.dumps(all_topics), 'languages': languages})
    else:
        return HttpResponse("You don't have permission to issue notifications from EntoLab, please contact MoveLab.")

#used by datatables
def get_order_clause(params_dict, translation_dict=None):
    order_clause = []
    try:
        order = params_dict['order']
        if len(order) > 0:
            for key in order:
                sort_dict = order[key]
                column_index_str = sort_dict['column']
                if translation_dict:
                    column_name = translation_dict[params_dict['columns'][int(column_index_str)]['data']]
                else:
                    column_name = params_dict['columns'][int(column_index_str)]['data']
                direction = sort_dict['dir']
                if direction != 'asc':
                    order_clause.append('-' + column_name)
                else:
                    order_clause.append(column_name)
    except KeyError:
        pass
    return order_clause

#used by datatables
def get_filter_clause(params_dict, fields, translation_dict=None):
    filter_clause = []
    try:
        q = params_dict['search']['value']
        if q != '':
            for field in fields:
                if translation_dict:
                    translated_field_name = translation_dict[field]
                    filter_clause.append( Q(**{translated_field_name+'__icontains':q}) )
                else:
                    filter_clause.append(Q(**{field + '__icontains': q}))
    except KeyError:
        pass
    return filter_clause


def generic_datatable_list_endpoint(request,search_field_list,queryset, classSerializer, field_translation_dict=None, order_translation_dict=None, paginate=True):

    draw = -1
    start = 0

    try:
        draw = request.GET['draw']
    except:
        pass
    try:
        start = request.GET['start']
    except:
        pass

    length = 25

    get_dict = parser.parse(request.GET.urlencode())

    order_clause = get_order_clause(get_dict, order_translation_dict)
    filter_clause = get_filter_clause(get_dict, search_field_list, field_translation_dict)

    if len(filter_clause) == 0:
        queryset = queryset.order_by(*order_clause)
    else:
        queryset = queryset.order_by(*order_clause).filter(functools.reduce(operator.or_, filter_clause))

    if paginate:
        paginator = Paginator(queryset, length)
        recordsTotal = queryset.count()
        recordsFiltered = recordsTotal
        page = int(start) / int(length) + 1
        serializer = classSerializer(paginator.page(page), many=True)

    else:
        serializer = classSerializer(queryset, many=True, context={'request': request})
        recordsTotal = queryset.count()
        recordsFiltered = recordsTotal

    return Response({'draw': draw, 'recordsTotal': recordsTotal, 'recordsFiltered': recordsFiltered, 'data': serializer.data})

@api_view(['GET'])
def aimalog_datatable(request):
    if request.method == 'GET':
        search_field_list = ('xvb','report_id','report_datetime','loc_code','cat_id','species','certainty','status','hit','review_species','review_status','review_datetime')
        queryset = Alert.objects.all()
        field_translation_list = {'xvb':'xvb','report_id':'report_id','report_datetime':'report_datetime','loc_code':'loc_code','cat_id':'cat_id','species':'species','certainty':'certainty','status':'status','hit':'hit','review_species':'review_species','review_status':'review_status','review_datetime':'review_datetime'}
        sort_translation_list = {'xvb':'xvb','report_id':'report_id','report_datetime':'report_datetime','loc_code':'loc_code','cat_id':'cat_id','species':'species','certainty':'certainty','status':'status','hit':'hit','review_species':'review_species','review_status':'review_status','review_datetime':'review_datetime'}
        response = generic_datatable_list_endpoint(request, search_field_list, queryset, DataTableAimalertSerializer, field_translation_list, sort_translation_list)
        return response

@api_view(['GET'])
def user_notifications_datatable(request):
    if request.method == 'GET':
        search_field_list = ('title_en', 'title_native')
        sent_to_topic = SentNotification.objects.filter(sent_to_topic__isnull=False).values('notification_id').distinct()
        queryset = Notification.objects.filter(id__in=sent_to_topic).order_by('-date_comment')
        field_translation_list = {'date_comment': 'date_comment', 'title_en': 'notification_content__title_en', 'title_native': 'notification_content__title_native'}
        sort_translation_list = {'date_comment': 'date_comment', 'title_en': 'notification_content__title_en', 'title_native': 'notification_content__title_native'}
        response = generic_datatable_list_endpoint(request, search_field_list, queryset, DataTableNotificationSerializer, field_translation_list, sort_translation_list)
        return response

@login_required
def notifications_table(request):
    return render(request, 'tigacrafting/notifications_table.html')


@login_required
def notification_detail(request,notification_id):
    notification_id = request.GET.get('notification_id', notification_id)
    notification = Notification.objects.get(id = notification_id)
    sent_notification = SentNotification.objects.filter(notification_id = notification_id).first()

    def clean_list(list_obj):
        #list_obj looks like [('uuid1',),]
        return str(list_obj).replace('(','').replace(')','').replace('[','').replace(']','').replace('\'','').replace(',,',',')[:-1]
        

    if sent_notification.sent_to_topic_id: #count the number of users subscribed
        potential_audience = UserSubscription.objects.aggregate(count = Count('id',filter=Q(topic_id = sent_notification.sent_to_topic_id)))['count']
        seen_by = AcknowledgedNotification.objects.aggregate(count = Count('id',filter=Q(notification_id = notification_id)))['count']
    else: # if not sent to topic then we return the user uuids 
        potential_audience = clean_list(list(SentNotification.objects.filter(notification_id=notification_id).values_list('sent_to_user_id')))
        seen_by = clean_list(list(AcknowledgedNotification.objects.filter(notification_id=notification_id).values_list('user_id')))

        # displaying 'seen by 0 users' looks better than '[] users'
        if len(seen_by)==0:
            seen_by = 0

    context = {'notification':notification, 'potential_audience':potential_audience,'seen_by':seen_by}
    return render(request,'tigacrafting/notification_detail.html',context)
