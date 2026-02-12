# coding=utf-8
from django.shortcuts import render, get_object_or_404
import json

from rest_framework.decorators import api_view

from tigacrafting.models import *
from tigaserver_app.models import Photo, Report
from django.db.models import Count
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.template.context_processors import csrf
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect
from django.urls import reverse
from django.conf import settings
from django.http import HttpResponse
from django.forms.models import modelformset_factory
from tigacrafting.forms import PhotoGrid
from tigaserver_app.models import Notification, EuropeCountry, SentNotification, NotificationTopic, TOPIC_GROUPS, Categories,AcknowledgedNotification, UserSubscription
from django.db.models import Q
from django.contrib.auth.models import User, Group
import urllib
from tigaserver_app.serializers import DataTableNotificationSerializer, DataTableAimalertSerializer
from django.db import transaction
from tigacrafting.forms import LicenseAgreementForm
import logging
from django.utils.translation import gettext as _
from tigacrafting.querystring_parser import parser
import functools
import operator

from decimal import *
from tigaserver_project.settings import *
from rest_framework.response import Response
from django.utils import timezone

#-----------------------------------#

logger_notification = logging.getLogger('mosquitoalert.notification')

@login_required
def entolab_license_agreement(request):
    if request.method == 'POST':
        form = LicenseAgreementForm(request.POST)
        if form.is_valid():
            request.user.userstat.license_accepted = True
            request.user.userstat.save()
            return HttpResponseRedirect('/experts')
    else:
        form = LicenseAgreementForm()
    return render(request, 'tigacrafting/entolab_license_agreement.html', {'form': form})

@login_required
def report_expiration(request, country_id=None):
    this_user = request.user

    if not this_user.userstat.is_superexpert():
        return HttpResponse("You need to be logged in as superexpert to view this page. If you have have been recruited as an expert and have lost your log-in credentials, please contact MoveLab.")

    qs = ExpertReportAnnotation.objects.blocking()

    country = None
    if country_id is not None:
        country = get_object_or_404(EuropeCountry, pk=country_id)
        qs = qs.filter(report__country=country)

    data_dict = {}
    for annotation in qs.select_related('user'):
        if annotation.user.username not in data_dict:
            data_dict[annotation.user.username] = []

        data_dict[annotation.user.username].append(
            {
                'report_uuid': annotation.report_id,
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
def reportannotation_formatter(var):
    if var.report.type == 'site':
        return {
            'report_id': var.report.version_UUID,
            'report_type': var.report.type,
            'givenToExpert': var.created.strftime("%d/%m/%Y - %H:%M:%S"),
            'lastModified': var.last_modified.strftime("%d/%m/%Y - %H:%M:%S"),
            'draftStatus': var.get_status_bootstrap(),
            'getScore': var.get_score(),
            'getCategory': var.get_category()
        }
    elif var.report.type == 'adult':
        return {
            'report_id': var.report.version_UUID,
            'report_type': var.report.type,
            'givenToExpert': var.created.strftime("%d/%m/%Y - %H:%M:%S"),
            'lastModified': var.last_modified.strftime("%d/%m/%Y - %H:%M:%S"),
            'draftStatus': var.get_status_bootstrap(),
            'getScore': var.get_score(),
            'getCategory': var.get_category_euro()
        }
    else:
        return {
            'report_id': var.report.version_UUID,
            'report_type': var.report.type,
            'givenToExpert': var.created.strftime("%d/%m/%Y - %H:%M:%S"),
            'lastModified': var.last_modified.strftime("%d/%m/%Y - %H:%M:%S"),
            'draftStatus': var.get_status_bootstrap(),
            'getScore': var.get_score(),
            'getCategory': var.get_category()
        }



@api_view(['GET'])
def expert_report_pending(request):
    user = request.query_params.get('u', None)
    u = User.objects.get(username=user)
    x = ExpertReportAnnotation.objects.filter(user=u, validation_complete=False)

    reports = []
    for var in x.select_related('report'):
        reports.append(reportannotation_formatter(var))

    context = {'pendingReports': reports}

    return Response(context)


@api_view(['GET'])
def expert_report_complete(request):
    user = request.query_params.get('u', None)
    u = User.objects.get(username=user)
    x = ExpertReportAnnotation.objects.filter(user=u, validation_complete=True)

    reports = []
    for var in x.select_related('report'):
        reports.append(reportannotation_formatter(var))

    context = {'completeReports': reports}

    return Response(context)

def auto_annotate_notsure(report: Report) -> None:
    ExpertReportAnnotation.create_auto_annotation(
        report=report,
        category=Categories.objects.get(pk=9),
        validation_value=None
    )

def auto_annotate_probably_albopictus(report: Report) -> None:
    ExpertReportAnnotation.create_auto_annotation(
        report=report,
        category=Categories.objects.get(pk=4),
        validation_value=ExpertReportAnnotation.VALIDATION_CATEGORY_PROBABLY
    )

def auto_annotate_albopictus(report: Report) -> None:
    ExpertReportAnnotation.create_auto_annotation(
        report=report,
        category=Categories.objects.get(pk=4),
        validation_value=ExpertReportAnnotation.VALIDATION_CATEGORY_DEFINITELY
    )

def auto_annotate_culex(report: Report) -> None:
    ExpertReportAnnotation.create_auto_annotation(
        report=report,
        category=Categories.objects.get(pk=10),
        validation_value=ExpertReportAnnotation.VALIDATION_CATEGORY_PROBABLY
    )

def auto_annotate_other_species(report: Report) -> None:
    ExpertReportAnnotation.create_auto_annotation(
        report=report,
        category=Categories.objects.get(pk=2),
        validation_value=None
    )

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
def picture_validation(request,tasks_per_page='300',visibility='visible', usr_note='', type='all', country='all', aithr='1.00'):
    this_user = request.user
    this_user_is_coarse = this_user.groups.filter(name='coarse_filter').exists()
    super_movelab = User.objects.get(pk=24)

    if not this_user_is_coarse:
        return HttpResponse("You need to be logged in as an expert member to view this page. If you have have been recruited as an expert and have lost your log-in credentials, please contact MoveLab.")

    args = {}
    args.update(csrf(request))
    PictureValidationFormSet = modelformset_factory(Report, form=PhotoGrid, extra=0, can_order=False)
    if request.method == 'POST':
        save_formset = request.POST.get('save_formset', "F")
        tasks_per_page = request.POST.get('tasks_per_page', tasks_per_page)
        if save_formset == "T":
            formset = PictureValidationFormSet(request.POST)
            if formset.is_valid():
                for f in formset:
                    report = f.save(commit=False)
                    #check that the report hasn't been assigned to anyone before saving, as a precaution to not hide assigned reports
                    who_has = report.get_who_has()
                    if who_has == '':
                        report.save()

###############-------------------------------- FastUpload --------------------------------###############

                        #print(f.cleaned_data)
                        if f.cleaned_data['fastUpload']:
                            #check that annotation does not exist, to avoid duplicates
                            if not ExpertReportAnnotation.objects.filter(report=report).filter(user=super_movelab).exists():
                                ExpertReportAnnotation.create_super_expert_approval(report=report)
###############------------------------------ FI FastUpload --------------------------------###############

                        if f.cleaned_data['other_species']:
                            auto_annotate_other_species(report)
                        if f.cleaned_data['probably_culex']:
                            auto_annotate_culex(report)
                        if f.cleaned_data['probably_albopictus']:
                            auto_annotate_probably_albopictus(report)
                        if f.cleaned_data['sure_albopictus']:
                            auto_annotate_albopictus(report)
                        if f.cleaned_data['not_sure']:
                            auto_annotate_notsure(report)

        page = request.POST.get('page')
        visibility = request.POST.get('visibility')
        usr_note = request.POST.get('usr_note')
        type = request.POST.get('type', type)
        country = request.POST.get('country', country)
        aithr = request.POST.get('aithr', aithr)
        if aithr == '':
            aithr = '0.75'

        if not page:
            page = request.GET.get('page',"1")
        return HttpResponseRedirect(reverse('picture_validation') + '?page=' + page + '&tasks_per_page='+tasks_per_page + '&visibility=' + visibility + '&usr_note=' + urllib.parse.quote_plus(usr_note) + '&type=' + type + '&country=' + country + '&aithr=' + aithr)
    else:
        tasks_per_page = request.GET.get('tasks_per_page', tasks_per_page)
        type = request.GET.get('type', type)
        country = request.GET.get('country', country)
        visibility = request.GET.get('visibility', visibility)
        usr_note = request.GET.get('usr_note', usr_note)
        aithr = request.GET.get('aithr', aithr)
        if aithr == '':
            aithr = '0.75'

    reports_qs = Report.objects.in_coarse_filter().order_by('-server_upload_time')

    if type == 'adult':
        type_readable = "Adults"
        reports_qs = reports_qs.filter(
            type=Report.TYPE_ADULT
        )
    elif type == 'site':
        type_readable = "Breeding sites - Storm drains"
        reports_qs = reports_qs.filter(type=Report.TYPE_SITE).filter(
            type=Report.TYPE_SITE,
            breeding_site_type=Report.BreedingSiteType.STORM_DRAIN
        )
    elif type == 'site-o':
        type_readable = "Breeding sites - Other"
        reports_qs = reports_qs.filter(
            type=Report.TYPE_SITE
        ).exclude(
            breeding_site_type=Report.BreedingSiteType.STORM_DRAIN
        )
    elif type == 'all':
        type_readable = "All"

    if visibility == 'visible':
        reports_qs = reports_qs.filter(hide=False)
    elif visibility == 'hidden':
        reports_qs = reports_qs.filter(hide=True)

    if usr_note and usr_note != '':
        reports_qs = reports_qs.filter(note__icontains=usr_note)

    if country and country != '':
        if country == 'all':
            country_readable = 'All'
        else:
            country = get_object_or_404(EuropeCountry, int(country))
            country_readable = country.name_engl
            reports_qs = reports_qs.filter(country=country)

    if aithr:
        reports_qs = reports_qs.filter(
            models.Q(identification_task__pred_insect_confidence__isnull=True)
            | models.Q(identification_task__pred_insect_confidence__lte=float(aithr))
        )

    reports_qs = reports_qs.prefetch_related('photos').select_related('country', 'identification_task').order_by('-server_upload_time')
    paginator = Paginator(
        reports_qs,
        int(tasks_per_page)
    )
    page_num = request.GET.get('page', 1)

    objects = paginator.get_page(page_num)
    page_query = objects
    page_query.ordered = True

    this_formset = PictureValidationFormSet(queryset=page_query)
    args['formset'] = this_formset
    args['objects'] = objects
    args['page'] = page_num
    args['pages'] = range(1, paginator.num_pages + 1)
    args['new_reports_unfiltered'] = page_query
    args['tasks_per_page'] = tasks_per_page
    args['aithr'] = aithr
    args['visibility'] = visibility
    args['usr_note'] = usr_note
    args['type'] = type
    args['country'] = country

    args['country_readable'] = country_readable

    args['countries'] = EuropeCountry.objects.all().order_by('name_engl')

    args['type_readable'] = type_readable

    args['n_query_records'] = reports_qs.count()

    range_list = [ n for n in range(5, 101, 5) ]
    args['tasks_per_page_choices'] = range_list + [200,300]

    return render(request, 'tigacrafting/photo_grid.html', args)

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
