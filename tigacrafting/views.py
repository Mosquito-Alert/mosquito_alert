# coding=utf-8
from pydoc import visiblename
from django.shortcuts import render, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
import requests
import json
from typing import Literal, Optional

from rest_framework.decorators import api_view

from tigacrafting.models import *
from tigaserver_app.models import Photo, Report, ReportResponse
import dateutil.parser
from django.db.models import Count
import pytz
from datetime import datetime
from django.db.models import Max,Min
from django.views.decorators.clickjacking import xframe_options_exempt
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from random import shuffle
from django.template.context_processors import csrf
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.conf import settings
from django.http import HttpResponse
from django.forms.models import modelformset_factory
from tigacrafting.forms import AnnotationForm, MovelabAnnotationForm, ExpertReportAnnotationForm, SuperExpertReportAnnotationForm, PhotoGrid
from tigaserver_app.models import Notification, NotificationContent, TigaUser, EuropeCountry, SentNotification, NotificationTopic, TOPIC_GROUPS, Categories,AcknowledgedNotification, UserSubscription
from zipfile import ZipFile
from io import BytesIO
from operator import attrgetter
from django.db.models import Q
from django.contrib.auth.models import User, Group
import urllib
import django.utils.html
from django.db import connection
from tigaserver_app.serializers import custom_render_notification, DataTableNotificationSerializer, DataTableAimalertSerializer
from django.contrib.gis.geos import GEOSGeometry
from django.db import transaction
from tigacrafting.forms import LicenseAgreementForm
import logging
from django.utils.translation import gettext as _
from tigacrafting.querystring_parser import parser
import functools
import operator
import math

#----------Metadades fotos----------#

import PIL.Image
from PIL.ExifTags import TAGS, GPSTAGS
from decimal import *
from tigaserver_project.settings import *
from rest_framework.response import Response
import re
from django.utils import timezone

#-----------------------------------#

logger_notification = logging.getLogger('mosquitoalert.notification')


def photos_to_tasks():
    these_photos = Photo.objects.filter(crowdcraftingtask=None).exclude(report__hide=True).visible()
    if these_photos:
        for p in these_photos:
            new_task = CrowdcraftingTask()
            new_task.photo = p
            new_task.save()


def import_tasks():
    errors = []
    warnings = []
    r = requests.get('http://crowdcrafting.org/app/Tigafotos/tasks/export?type=task&format=json')
    try:
        task_array = json.loads(r.text)
    except ValueError:
        zipped_file = ZipFile(BytesIO(r.content))
        task_array = json.loads(zipped_file.open(zipped_file.namelist()[0]).read())
    last_task_id = CrowdcraftingTask.objects.all().aggregate(Max('task_id'))['task_id__max']
    if last_task_id:
        new_tasks = filter(lambda x: x['id'] > last_task_id, task_array)
    else:
        new_tasks = task_array
    for task in new_tasks:
        existing_task = CrowdcraftingTask.objects.filter(task_id=task['id'])
        if not existing_task:
            existing_empty_task = CrowdcraftingTask.objects.filter(photo=task['info'][u'\ufeffid'])
            if not existing_empty_task:
                task_model = CrowdcraftingTask()
                task_model.task_id = task['id']
                existing_photo = Photo.objects.filter(id=int(task['info'][u'\ufeffid']))
                if existing_photo:
                    this_photo = Photo.objects.get(id=task['info'][u'\ufeffid'])
                    # check for tasks that already have this photo: There should not be any BUT I accidentially added photos 802-810 in both the first and second crowdcrafting task batches
                    if CrowdcraftingTask.objects.filter(photo=this_photo).count() > 0:
                        # do nothing if photo id beteen 802 and 810 since I already know about this
                        if this_photo.id in range(802, 811):
                            pass
                        else:
                            errors.append('Task with Photo ' + str(this_photo.id) + ' already exists. Not importing this task.')
                    else:
                        task_model.photo = this_photo
                        task_model.save()
                else:
                    errors.append('Photo with id=' + task['info'][u'\ufeffid'] + ' does not exist.')
            else:
                existing_empty_task.task_id = task['id']
                existing_photo = Photo.objects.filter(id=int(task['info'][u'\ufeffid']))
                if existing_photo:
                    this_photo = Photo.objects.get(id=task['info'][u'\ufeffid'])
                    # check for tasks that already have this photo: There should not be any BUT I accidentially added photos 802-810 in both the first and second crowdcrafting task batches
                    if CrowdcraftingTask.objects.filter(photo=this_photo).count() > 0:
                        # do nothing if photo id beteen 802 and 810 since I already know about this
                        if this_photo.id in range(802, 811):
                            pass
                        else:
                            errors.append('Task with Photo ' + str(this_photo.id) + ' already exists. Not importing this task.')
                    else:
                        existing_empty_task.photo = this_photo
                        existing_empty_task.save()
                else:
                    errors.append('Photo with id=' + task['info'][u'\ufeffid'] + ' does not exist.')
        else:
            warnings.append('Task ' + str(existing_task[0].task_id) + ' already exists, not saved.')
    # write errors and warnings to files that we can check
    if len(errors) > 0 or len(warnings) > 0:
        barcelona = pytz.timezone('Europe/Paris')
        ef = open(settings.MEDIA_ROOT + 'crowdcrafting_error_log.html', 'a')
        if len(errors) > 0:
            ef.write('<h1>tigacrafting.views.import_tasks errors</h1><p>' + barcelona.localize(datetime.datetime.now()).strftime('%Y-%m-%d %H:%M:%S UTC%z') + '</p><p>' + '</p><p>'.join(errors) + '</p>')
        if len(warnings) > 0:
            ef.write('<h1>tigacrafting.views.import_tasks warnings</h1><p>' + barcelona.localize(datetime.datetime.now()).strftime('%Y-%m-%d %H:%M:%S UTC%z') + '</p><p>' + '</p><p>'.join(warnings) + '</p>')
        ef.close()
        print( '\n'.join(errors) )
        print( '\n'.join(warnings) )
    return {'errors': errors, 'warnings': warnings}


def import_task_responses():
    errors = []
    warnings = []
    r = requests.get('http://crowdcrafting.org/app/Tigafotos/tasks/export?type=task_run&format=json')
    try:
        response_array = json.loads(r.text)
    except ValueError:
        zipped_file = ZipFile(BytesIO(r.content))
        response_array = json.loads(zipped_file.open(zipped_file.namelist()[0]).read())
    last_response_id = CrowdcraftingResponse.objects.all().aggregate(Max('response_id'))['response_id__max']
    if last_response_id:
        new_responses = filter(lambda x: x['id'] > last_response_id, response_array)
    else:
       new_responses = response_array
    for response in new_responses:
        existing_response = CrowdcraftingResponse.objects.filter(response_id=int(response['id']))
        if existing_response:
            warnings.append('Response to task ' + str(response['task_id']) + ' by user ' + str(response['user_id']) + ' already exists. Skipping this response.')
        else:
            info_dic = {}
            info_fields = response['info'].replace('{', '').replace(' ', '').replace('}', '').split(',')
            for info_field in info_fields:
                info_dic[info_field.split(':')[0]] = info_field.split(':')[1]
            response_model = CrowdcraftingResponse()
            response_model.response_id = int(response['id'])
            creation_time = dateutil.parser.parse(response['created'])
            creation_time_localized = pytz.utc.localize(creation_time)
            response_model.created = creation_time_localized
            finish_time = dateutil.parser.parse(response['finish_time'])
            finish_time_localized = pytz.utc.localize(finish_time)
            response_model.finish_time = finish_time_localized
            response_model.mosquito_question_response = info_dic['mosquito']
            response_model.tiger_question_response = info_dic['tiger']
            response_model.site_question_response = info_dic['site']
            response_model.user_ip = response['user_ip']
            response_model.user_lang = info_dic['user_lang']
            existing_task = CrowdcraftingTask.objects.filter(task_id=response['task_id'])
            if existing_task:
                print( 'existing task' )
                this_task = CrowdcraftingTask.objects.get(task_id=response['task_id'])
                response_model.task = this_task
            else:
                import_tasks()
                warnings.append('Task ' + str(response['task_id']) + ' did not exist, so import_tasks was called.')
                existing_task = CrowdcraftingTask.objects.filter(task_id=response['task_id'])
                if existing_task:
                    this_task = CrowdcraftingTask.objects.get(task_id=response['task_id'])
                    response_model.task = this_task
                else:
                    errors.append('Cannot seem to import task ' + str(response['task_id']))
                    continue
            existing_user = CrowdcraftingUser.objects.filter(user_id=response['user_id'])
            if existing_user:
                this_user = CrowdcraftingUser.objects.get(user_id=response['user_id'])
                response_model.user = this_user
            else:
                this_user = CrowdcraftingUser()
                this_user.user_id = response['user_id']
                this_user.save()
                response_model.user = this_user
            response_model.save()
    # write errors and warnings to files that we can check
    barcelona = pytz.timezone('Europe/Paris')
    if len(errors) > 0 or len(warnings) > 0:
        ef = open(settings.MEDIA_ROOT + 'crowdcrafting_error_log.html', 'a')
        if len(errors) > 0:
            ef.write('<h1>tigacrafting.views.import_task_responses errors</h1><p>' + barcelona.localize(datetime.datetime.now()).strftime('%Y-%m-%d %H:%M:%S UTC%z') + '</p><p>' + '</p><p>'.join(errors) + '</p>')
        if len(warnings) > 0:
            ef.write('<h1>tigacrafting.views.import_task_responses warnings</h1><p>' + barcelona.localize(datetime.datetime.now()).strftime('%Y-%m-%d %H:%M:%S UTC%z') + '</p><p>' + '</p><p>'.join(warnings) + '</p>')
        ef.close()
      #  print '\n'.join(errors)
      #  print '\n'.join(warnings)
    return {'errors': errors, 'warnings': warnings}


def show_processing(request):
    return render(request, 'tigacrafting/please_wait.html')


def filter_tasks(tasks):
    tasks_filtered = filter(lambda x: not x.photo.report.deleted, tasks)
    return tasks_filtered

def filter_spain_reports(reports, sort=True):
    if sort:
        reports_filtered = sorted( filter(lambda x: x.is_spain, reports), key=attrgetter('n_annotations'), reverse=True)
    else:
        reports_filtered = filter(lambda x: x.is_spain, reports)
    return reports_filtered


def filter_eu_reports(reports, sort=True):
    if sort:
        reports_filtered = sorted(filter(lambda x: not x.is_spain, reports), key=attrgetter('n_annotations'), reverse=True)
    else:
        reports_filtered = filter(lambda x: not x.is_spain, reports)
    return reports_filtered


def filter_reports_for_superexpert(reports):
    reports_filtered = reports.non_deleted()
    reports_filtered = filter(lambda x: len(list(filter(lambda y: y.is_expert() and y.validation_complete, x.expert_report_annotations.all()))) >= 3, reports_filtered)
    return reports_filtered


@xframe_options_exempt
def show_validated_photos(request, type='tiger'):
    title_dic = {'mosquito': 'Mosquito Validation Results', 'site': 'Breeding Site Validation Results', 'tiger': 'Tiger Mosquito Validation Results'}
    question_dic = {'mosquito': 'Do you see a mosquito in this photo?', 'site': 'Do you see a potential tiger mosquito breeding site in this photo?', 'tiger': 'Is this a tiger mosquito?'}
    validation_score_dic = {'mosquito': 'mosquito_validation_score', 'site': 'site_validation_score', 'tiger': 'tiger_validation_score'}
    individual_responses_dic = {'mosquito': 'mosquito_individual_responses_html', 'site': 'site_individual_responses_html', 'tiger': 'tiger_individual_responses_html'}
    import_task_responses()
    validated_tasks = CrowdcraftingTask.objects.annotate(n_responses=Count('responses')).filter(n_responses__gte=30).exclude(photo__report__hide=True).exclude(photo__hide=True)
    validated_tasks_filtered = filter_tasks(validated_tasks)
    validated_task_array = sorted(map(lambda x: {'id': x.id, 'report_type': x.photo.report.type, 'report_creation_time': x.photo.report.creation_time.strftime('%d %b %Y, %H:%M %Z'), 'lat': x.photo.report.lat, 'lon':  x.photo.report.lon, 'photo_image': x.photo.medium_image_(), 'validation_score': round(getattr(x, validation_score_dic[type]), 2), 'neg_validation_score': -1*round(getattr(x, validation_score_dic[type]), 2), 'individual_responses_html': getattr(x, individual_responses_dic[type])}, list(validated_tasks_filtered)), key=lambda x: -x['validation_score'])
    paginator = Paginator(validated_task_array, 25)
    page = request.GET.get('page')
    try:
        these_validated_tasks = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        these_validated_tasks = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        these_validated_tasks = paginator.page(paginator.num_pages)
    context = {'type': type, 'title': title_dic[type], 'n_tasks': len(validated_task_array), 'question': question_dic[type], 'validated_tasks': these_validated_tasks}
    return render(request, 'tigacrafting/validated_photos.html', context)


@login_required
def annotate_tasks(request, how_many=None, which='new', scroll_position=''):
    this_user = request.user
    args = {}
    args.update(csrf(request))
    args['scroll_position'] = scroll_position
    AnnotationFormset = modelformset_factory(Annotation, form=AnnotationForm, extra=0)
    if request.method == 'POST':
        scroll_position = request.POST.get("scroll_position", '0')
        formset = AnnotationFormset(request.POST)
        if formset.is_valid():
            formset.save()
            return HttpResponseRedirect(reverse('annotate_tasks_scroll_position', kwargs={'which': 'working_on', 'scroll_position': scroll_position}))
        else:
            return HttpResponse('error')
    else:
        if which == 'noted_only':
            Annotation.objects.filter(working_on=True).update(working_on=False)
            this_queryset = Annotation.objects.filter(user=request.user, value_changed=False).exclude(notes="")
            this_queryset.update(working_on=True)
            this_formset = AnnotationFormset(queryset=this_queryset)
        if which == 'completed':
            Annotation.objects.filter(working_on=True).update(working_on=False)
            this_queryset = Annotation.objects.filter(user=request.user).exclude( tiger_certainty_percent=None).exclude(value_changed=False)
            this_queryset.update(working_on=True)
            this_formset = AnnotationFormset(queryset=this_queryset)
        if which == 'working_on':
            this_formset = AnnotationFormset(queryset=Annotation.objects.filter(user=request.user, working_on=True))
        if which == 'new':
            import_task_responses()
            annotated_task_ids = Annotation.objects.filter(user=this_user).exclude(tiger_certainty_percent=None).exclude(value_changed=False).values('task__id')
            validated_tasks = CrowdcraftingTask.objects.exclude(id__in=annotated_task_ids).exclude(photo__report__hide=True).exclude(photo__hide=True).filter(photo__report__type='adult').annotate(n_responses=Count('responses')).filter(n_responses__gte=30)
            validated_tasks_filtered = filter_tasks(validated_tasks)
            shuffle(validated_tasks_filtered)
            if how_many is not None:
                task_sample = validated_tasks_filtered[:int(how_many)]
            else:
                task_sample = validated_tasks_filtered
            # reset working_on annotations
            Annotation.objects.filter(working_on=True).update(working_on=False)
            # set working on for existing annotations:
            Annotation.objects.filter(user=this_user, task__in=task_sample).update(working_on=True)
            # make blank annotations for this user as needed
            for this_task in task_sample:
                if not Annotation.objects.filter(user=this_user, task=this_task).exists():
                    new_annotation = Annotation(user=this_user, task=this_task, working_on=True)
                    new_annotation.save()
            this_formset = AnnotationFormset(queryset=Annotation.objects.filter(user=request.user, task__in=task_sample))
        args['formset'] = this_formset
        return render(request, 'tigacrafting/expert_validation.html', args)


@login_required
def movelab_annotation(request, scroll_position='', tasks_per_page='50', type='all'):
    this_user = request.user
    if request.user.groups.filter(name='movelab').exists():
        args = {}
        args.update(csrf(request))
        args['scroll_position'] = scroll_position
        AnnotationFormset = modelformset_factory(MoveLabAnnotation, form=MovelabAnnotationForm, extra=0)
        if request.method == 'POST':
            scroll_position = request.POST.get("scroll_position", '0')
            formset = AnnotationFormset(request.POST)
            if formset.is_valid():
                formset.save()
                page = request.GET.get('page')
                if not page:
                    page = '1'
                if type == 'pending':
                    return HttpResponseRedirect(reverse('movelab_annotation_pending_scroll_position', kwargs={'tasks_per_page': tasks_per_page, 'scroll_position': scroll_position}) + '?page='+page)
                else:
                    return HttpResponseRedirect(reverse('movelab_annotation_scroll_position', kwargs={'tasks_per_page': tasks_per_page, 'scroll_position': scroll_position}) + '?page='+page)
            else:
                return HttpResponse('error')
        else:
            photos_to_tasks()
            import_tasks()
            tasks_without_annotations_unfiltered = CrowdcraftingTask.objects.exclude(photo__report__hide=True).exclude(photo__hide=True).filter(movelab_annotation=None)
            tasks_without_annotations = filter_tasks(tasks_without_annotations_unfiltered)
            for this_task in tasks_without_annotations:
                new_annotation = MoveLabAnnotation(task=this_task)
                new_annotation.save()
            all_annotations = MoveLabAnnotation.objects.all().order_by('id')
            if type == 'pending':
                all_annotations = all_annotations.exclude(tiger_certainty_category__in=[-2, -1, 0, 1, 2])
            paginator = Paginator(all_annotations, int(tasks_per_page))
            page = request.GET.get('page')
            try:
                objects = paginator.page(page)
            except PageNotAnInteger:
                objects = paginator.page(1)
            except EmptyPage:
                objects = paginator.page(paginator.num_pages)
            page_query = all_annotations.filter(id__in=[object.id for object in objects])
            this_formset = AnnotationFormset(queryset=page_query)
            args['formset'] = this_formset
            args['objects'] = objects
            args['pages'] = range(1, objects.paginator.num_pages+1)
            args['tasks_per_page_choices'] = range(25, min(200, all_annotations.count())+1, 25)
        return render(request, 'tigacrafting/movelab_validation.html', args)
    else:
        return HttpResponse("You need to be logged in as a MoveLab member to view this page.")


@login_required
def movelab_annotation_pending(request, scroll_position='', tasks_per_page='50', type='pending'):
    this_user = request.user
    if request.user.groups.filter(name='movelab').exists():
        args = {}
        args.update(csrf(request))
        args['scroll_position'] = scroll_position
        AnnotationFormset = modelformset_factory(MoveLabAnnotation, form=MovelabAnnotationForm, extra=0)
        if request.method == 'POST':
            scroll_position = request.POST.get("scroll_position", '0')
            formset = AnnotationFormset(request.POST)
            if formset.is_valid():
                formset.save()
                page = request.GET.get('page')
                if not page:
                    page = '1'
                if type == 'pending':
                    return HttpResponseRedirect(reverse('movelab_annotation_pending_scroll_position', kwargs={'tasks_per_page': tasks_per_page, 'scroll_position': scroll_position}) + '?page='+page)
                else:
                    return HttpResponseRedirect(reverse('movelab_annotation_scroll_position', kwargs={'tasks_per_page': tasks_per_page, 'scroll_position': scroll_position}) + '?page='+page)
            else:
                return HttpResponse('error')
        else:
            photos_to_tasks()
            import_tasks()
            tasks_without_annotations_unfiltered = CrowdcraftingTask.objects.exclude(photo__report__hide=True).exclude(photo__hide=True).filter(movelab_annotation=None)
            tasks_without_annotations = filter_tasks(tasks_without_annotations_unfiltered)
            for this_task in tasks_without_annotations:
                new_annotation = MoveLabAnnotation(task=this_task)
                new_annotation.save()
            all_annotations = MoveLabAnnotation.objects.all().order_by('id')
            if type == 'pending':
                all_annotations = all_annotations.exclude(tiger_certainty_category__in=[-2, -1, 0, 1, 2])
            paginator = Paginator(all_annotations, int(tasks_per_page))
            page = request.GET.get('page')
            try:
                objects = paginator.page(page)
            except PageNotAnInteger:
                objects = paginator.page(1)
            except EmptyPage:
                objects = paginator.page(paginator.num_pages)
            page_query = all_annotations.filter(id__in=[object.id for object in objects])
            this_formset = AnnotationFormset(queryset=page_query)
            args['formset'] = this_formset
            args['objects'] = objects
            args['pages'] = range(1, objects.paginator.num_pages+1)
            args['tasks_per_page_choices'] = range(25, min(200, all_annotations.count())+1, 25)
        return render(request, 'tigacrafting/movelab_validation.html', args)
    else:
        return HttpResponse("You need to be logged in as a MoveLab member to view this page.")

ITALY_GEOMETRY = GEOSGeometry('{"type": "Polygon","coordinates": [[[7.250976562499999,43.70759350405294],[8.96484375,44.071800467511565],[10.96435546875,41.95131994679697],[7.822265625000001,41.0130657870063],[8.1298828125,38.788345355085625],[11.865234375,37.735969208590504],[14.1064453125,36.70365959719456],[14.985351562499998,36.31512514748051],[18.80859375,40.27952566881291],[12.45849609375,44.5278427984555],[13.86474609375,45.413876460821086],[14.04052734375,46.51351558059737],[12.238769531249998,47.264320080254805],[6.8994140625,46.10370875598026],[6.43798828125,45.120052841530544],[7.250976562499999,43.70759350405294]]]}')


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
def predefined_messages(request):
    langs = []
    for elem in settings.LANGUAGES:
        langs.append({"val":elem[0],"txt":elem[1]})
    langs.sort(key=lambda x: x.get("txt"))
    return render(request, 'tigacrafting/predefined_messages.html', {'langs': langs})



def update_pending_data(country):
    country.pending_crisis_reports = IdentificationTask.objects.backlog().filter(report__country=country).in_exclusivity_period(state=False).count()
    country.last_crisis_report_n_update = timezone.now()
    country.save()


def get_cached_country_pending_crisis_reports(country):
    if country.pending_crisis_reports is None or country.last_crisis_report_n_update is None:
        update_pending_data(country)
    elif country.last_crisis_report_n_update is not None:
        try:
            last_country_validation_activity = ExpertReportAnnotation.objects.filter(report__country=country).latest('created').created
            if country.last_crisis_report_n_update < last_country_validation_activity:
                update_pending_data(country)
        except ExpertReportAnnotation.DoesNotExist:
            country.pending_crisis_reports
    return country.pending_crisis_reports


def pending_reports_by_country():
    country_qs = EuropeCountry.objects.exclude(is_bounding_box=True)
    data = {}
    for country in country_qs:
        available_reports_country = get_cached_country_pending_crisis_reports(country)
        data[country.gid] = {"n": available_reports_country, "x": country.geom.centroid.x, "y": country.geom.centroid.y, "name": country.name_engl}
    return data


@login_required
def expert_geo_report_assign(request):
    this_user = request.user
    if this_user.userstat.crisis_mode:
        count_data = pending_reports_by_country()
        return render(request, 'tigacrafting/geo_report_assign.html', { 'count_data': json.dumps(count_data) })
    else:
        return HttpResponse("You don't have emergency mode permissions, so you can't see this page. Please contact your administrator.")


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
def expert_report_annotation(request, scroll_position='', tasks_per_page='10', note_language='es', load_new_reports='F', year='all', orderby='date', tiger_certainty='all', site_certainty='all', pending='na', checked='na', status='all', final_status='na', max_pending=5, max_given=3, version_uuid='na', linked_id='na', ns_exec='all', edit_mode='off', tags_filter='na'):
    this_user = request.user

    if settings.SHOW_USER_AGREEMENT_ENTOLAB:
        if this_user.userstat:
            if not this_user.userstat.has_accepted_license():
                return HttpResponseRedirect(reverse('entolab_license_agreement'))
        else:
            return HttpResponse("There is a problem with your current user. Please contact the EntoLab admin at " + settings.ENTOLAB_ADMIN)

    this_user_is_expert = this_user.userstat.is_expert()
    this_user_is_superexpert = this_user.userstat.is_superexpert()

    if not (this_user_is_expert or this_user_is_superexpert):
        return HttpResponse("You need to be logged in as an expert member to view this page. If you have have been recruited as an expert and have lost your log-in credentials, please contact MoveLab.")

    args = {}
    args.update(csrf(request))
    args['scroll_position'] = scroll_position

    if this_user_is_superexpert:
        AnnotationFormset = modelformset_factory(ExpertReportAnnotation, form=SuperExpertReportAnnotationForm, extra=0, can_order=False)
    else:
        AnnotationFormset = modelformset_factory(ExpertReportAnnotation, form=ExpertReportAnnotationForm, extra=0, can_order=False)

    if request.method == 'POST':
        scroll_position = request.POST.get("scroll_position", '0')
        orderby = request.POST.get('orderby', orderby)
        tiger_certainty = request.POST.get('tiger_certainty', tiger_certainty)
        site_certainty = request.POST.get('site_certainty', site_certainty)
        pending = request.POST.get('pending', pending)
        status = request.POST.get('status', status)
        final_status = request.POST.get('final_status', final_status)
        version_uuid = request.POST.get('version_uuid', version_uuid)
        linked_id = request.POST.get('linked_id', linked_id)
        ns_exec = request.POST.get('ns_exec', ns_exec)
        tags_filter = request.POST.get('tags_filter', tags_filter)
        checked = request.POST.get('checked', checked)
        tasks_per_page = request.POST.get('tasks_per_page', tasks_per_page)
        note_language = request.GET.get('note_language', "es")
        load_new_reports = request.POST.get('load_new_reports', load_new_reports)
        save_formset = request.POST.get('save_formset', "F")
        if save_formset == "T":
            formset = AnnotationFormset(request.POST)
            if formset.is_valid():
                for f in formset:
                    one_form = f.save(commit=False)
                    one_form.save()
                    f.save_m2m()
            else:
                return render(request, 'tigacrafting/formset_errors.html', {'formset': formset})
        page = request.POST.get('page')
        if not page:
            page = '1'
        return HttpResponseRedirect(reverse('expert_report_annotation') + '?page='+page+'&tasks_per_page='+tasks_per_page+'&note_language=' + note_language + '&scroll_position='+scroll_position+(('&pending='+pending) if pending else '') + (('&checked='+checked) if checked else '') + (('&final_status='+final_status) if final_status else '') + (('&version_uuid='+version_uuid) if version_uuid else '') + (('&linked_id='+linked_id) if linked_id else '') + (('&orderby='+orderby) if orderby else '') + (('&tiger_certainty='+tiger_certainty) if tiger_certainty else '') + (('&site_certainty='+site_certainty) if site_certainty else '') + (('&status='+status) if status else '') + (('&load_new_reports='+load_new_reports) if load_new_reports else '') + (('&tags_filter=' + urllib.parse.quote_plus(tags_filter)) if tags_filter else ''))
    else:
        tasks_per_page = request.GET.get('tasks_per_page', tasks_per_page)
        note_language = request.GET.get('note_language', note_language)
        scroll_position = request.GET.get('scroll_position', scroll_position)
        orderby = request.GET.get('orderby', orderby)
        tiger_certainty = request.GET.get('tiger_certainty', tiger_certainty)
        site_certainty = request.GET.get('site_certainty', site_certainty)
        pending = request.GET.get('pending', pending)
        status = request.GET.get('status', status)
        final_status = request.GET.get('final_status', final_status)
        version_uuid = request.GET.get('version_uuid', version_uuid)
        linked_id = request.GET.get('linked_id', linked_id)
        ns_exec = request.GET.get('ns_exec', ns_exec)
        tags_filter = request.GET.get('tags_filter', tags_filter)
        checked = request.GET.get('checked', checked)
        load_new_reports = request.GET.get('load_new_reports', load_new_reports)
        edit_mode = request.GET.get('edit_mode', edit_mode)

        task_qs = IdentificationTask.objects

        if load_new_reports == 'T' or this_user_is_superexpert:
            this_user.userstat.assign_reports()

        if this_user_is_expert:
            if (version_uuid == 'na' and linked_id == 'na' and tags_filter == 'na') and (not pending or pending == 'na'):
                pending = 'pending'

        if this_user_is_superexpert:
            if (version_uuid == 'na' and linked_id == 'na' and tags_filter == 'na') and (not final_status or final_status == 'na'):
                final_status = 'public'
            if (version_uuid == 'na' and linked_id == 'na' and tags_filter == 'na') and (not checked or checked == 'na'):
                checked = 'unchecked'

            user_tasks = task_qs.filter(assignees=this_user)

            args['n_flagged'] = user_tasks.done().filter(is_flagged=True).count()
            args['n_hidden'] = user_tasks.done().filter(is_safe=False).count()
            args['n_public'] = user_tasks.done().filter(is_flagged=False, is_safe=True).count()

            user_report_annotations = ExpertReportAnnotation.objects.filter(
                user=this_user,
                identification_task__in=user_tasks,
            )
            args['n_unchecked'] = user_report_annotations.filter(validation_complete=False).count()
            args['n_confirmed'] = user_report_annotations.filter(validation_complete=True, revise=False).count()
            args['n_revised'] = user_report_annotations.filter(validation_complete=True, revise=True).count()

        all_annotations = this_user.expert_report_annotations.all()
        if version_uuid and version_uuid != 'na':
            all_annotations = all_annotations.filter(report__pk=version_uuid)
        if linked_id and linked_id != 'na':
            all_annotations = all_annotations.filter(linked_id=linked_id)
        if tags_filter and tags_filter != 'na' and tags_filter!='':
            tags_array = tags_filter.split(",")
            # we must go up to Report to filter tags, because you don't want to filter only your own tags but the tag that
            # any expert has put on the report
            # these are all (not only yours, but also) the reports that contain the filtered tag
            # we want the annotations of the reports which contain the tag(s)
            all_annotations = all_annotations.filter(tags__name__in=tags_array)
        if (not version_uuid or version_uuid == 'na') and (not linked_id or linked_id == 'na') and (not tags_filter or tags_filter == 'na' or tags_filter==''):
            if year and year != 'all':
                try:
                    this_year = int(year)
                    all_annotations = all_annotations.filter(report__server_upload_time__year=this_year)
                except ValueError:
                    pass
            if tiger_certainty and tiger_certainty != 'all':
                try:
                    this_certainty = int(tiger_certainty)
                    all_annotations = all_annotations.filter(category__id=this_certainty)
                except ValueError:
                    pass
            if site_certainty and site_certainty != 'all':
                try:
                    this_certainty = int(site_certainty)
                    all_annotations = all_annotations.filter(site_certainty_category=this_certainty)
                except ValueError:
                    pass
            if ns_exec and ns_exec != 'all':
                try:
                    this_exec = int(ns_exec)
                    all_annotations = all_annotations.filter(validation_complete_executive=True, user_id=this_exec)
                except ValueError:
                    pass

            if pending == "complete":
                all_annotations = all_annotations.filter(validation_complete=True)
            elif pending == 'pending':
                all_annotations = all_annotations.filter(validation_complete=False)
            elif pending == 'favorite':
                all_annotations = all_annotations.filter(report__favorites__user=this_user)
            if status == "flagged":
                all_annotations = all_annotations.filter(status=ExpertReportAnnotation.STATUS_FLAGGED)
            elif status == "hidden":
                all_annotations = all_annotations.filter(status=ExpertReportAnnotation.STATUS_HIDDEN)
            elif status == "public":
                all_annotations = all_annotations.filter(status=ExpertReportAnnotation.STATUS_PUBLIC)

            if this_user_is_superexpert:
                if checked == "unchecked":
                    all_annotations = all_annotations.filter(validation_complete=False)
                elif checked == "confirmed":
                    all_annotations = all_annotations.filter(validation_complete=True, revise=False)
                elif checked == "revised":
                    all_annotations = all_annotations.filter(validation_complete=True, revise=True)
                elif checked == "favorite":
                    all_annotations = all_annotations.filter(report__favorites__user=this_user)

                if final_status == "flagged":
                    all_annotations = all_annotations.filter(
                        identification_task__is_flagged=True
                    )
                elif final_status == "hidden":
                    all_annotations = all_annotations.filter(
                        identification_task__is_safe=False
                    )
                elif final_status == "public":
                    all_annotations = all_annotations.filter(
                        identification_task__is_safe=True,
                        identification_task__is_flagged=False
                    )

        all_annotations = all_annotations.order_by('-report__server_upload_time')
        if orderby == "tiger_score":
            all_annotations = all_annotations.order_by('category__name')

        paginator = Paginator(all_annotations, int(tasks_per_page))
        page_num = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_num)

        this_formset = AnnotationFormset(queryset=page_obj.object_list)
        args['formset'] = this_formset
        args['objects'] = page_obj
        args['pages'] = paginator.page_range
        current_pending = this_user.userstat.num_pending_annotations
        args['n_pending'] = current_pending
        n_complete = this_user.userstat.num_completed_annotations
        args['n_complete'] = n_complete
        n_favorites = FavoritedReports.objects.filter(user=this_user).count()
        args['n_favorites'] = n_favorites
        args['n_total'] = n_complete + current_pending
        args['year'] = year
        args['orderby'] = orderby
        args['tiger_certainty'] = tiger_certainty
        if tiger_certainty:
            if tiger_certainty != 'all':
                try:
                    this_certainty = int(tiger_certainty)
                    c = Categories.objects.get(pk=this_certainty)
                    args['tiger_certainty_label'] = c.name
                except ValueError:
                    pass
            else:
                args['tiger_certainty_label'] = 'all'
        args['site_certainty'] = site_certainty
        args['pending'] = pending
        args['checked'] = checked
        args['status'] = status
        args['final_status'] = final_status
        args['version_uuid'] = version_uuid
        args['linked_id'] = linked_id
        args['ns_exec'] = ns_exec
        if ns_exec:
            if ns_exec != 'all':
                try:
                    exec_validator_id = int(ns_exec)
                    exec_validator = User.objects.get(pk=exec_validator_id)
                    args['exec_validated_label'] = "{0} - {1}".format(exec_validator.username, exec_validator.userstat.national_supervisor_of.name_engl )
                except:
                    pass
            else:
                args['exec_validated_label'] = 'N/A'
        args['tags_filter'] = tags_filter
        args['my_linked_ids'] = this_user.expert_report_annotations.filter(report__type='adult').values('linked_id').distinct()
        args['tasks_per_page'] = tasks_per_page
        args['note_language'] = note_language
        args['scroll_position'] = scroll_position
        args['edit_mode'] = edit_mode
        n_query_records = all_annotations.count()
        args['n_query_records'] = n_query_records
        args['tasks_per_page_choices'] = range(5, min(100, n_query_records)+1, 5)
        args['category_list'] = Categories.objects.order_by('name')
        args['complex_list'] = Complex.objects.order_by('description')
        args['other_species_insects'] = OtherSpecies.objects.filter(category='Other insects').order_by('name')
        args['other_species_culicidae'] = OtherSpecies.objects.filter(category='Culicidae').order_by('ordering','name')

        args['country_name'] = EuropeCountry.objects.filter(
            models.Exists(
                UserStat.objects.filter(
                    user__groups__name='expert',
                    native_of_id=models.OuterRef('gid')
                )
            )
        ).order_by('name_engl').values('name_engl','iso3_code')

        args['ns_list'] = User.objects.filter(userstat__national_supervisor_of__isnull=False).order_by('userstat__national_supervisor_of__name_engl')

        return render(request, 'tigacrafting/expert_report_annotation.html' if this_user_is_expert else 'tigacrafting/superexpert_report_annotation.html', args)

@login_required
def single_report_view(request,version_uuid):
    this_user = request.user
    version_uuid = request.GET.get('version_uuid', version_uuid)
    report = Report.objects.get(pk=version_uuid)
    who_has_list = []
    if report:
        for ano in report.expert_report_annotations.select_related('user').all():
            if ano.user.username != this_user.username and not ano.user.userstat.is_superexpert():
                who_has_list.append( '<span class="label ' + ('label-success' if ano.validation_complete else 'label-warning') + '" data-toggle="tooltip" data-placement="bottom" title="' + (('validated by expert') if ano.validation_complete else ('pending with expert')) + '">expert <span class="glyphicon ' + ('glyphicon-check' if ano.validation_complete else 'glyphicon-time') + '"></span></span>' )
            else:
                who_has_list.append('<span class="label ' + ('label-success' if ano.validation_complete else 'label-warning') + '" data-toggle="tooltip" data-placement="bottom" title="' + (('validated by ' + ano.user.username) if ano.validation_complete else ('pending with ' + ano.user.username)) + '">' + ano.user.username + '<span class="glyphicon ' + ('glyphicon-check' if ano.validation_complete else 'glyphicon-time') + '"></span></span>')
    context = {'reports': [report,], 'version_uuid' : version_uuid, 'this_user': this_user.username, 'who_has_list': who_has_list}
    return render(request, 'tigacrafting/single_report_view.html', context)


@login_required
def expert_report_status(request, reports_per_page=10, version_uuid=None, linked_id=None):
    this_user = request.user
    if this_user.groups.filter(Q(name='superexpert') | Q(name='movelab')).exists():
        version_uuid = request.GET.get('version_uuid', version_uuid)
        reports_per_page = request.GET.get('reports_per_page', reports_per_page)

        if version_uuid and version_uuid != 'na':
            reports = Report.objects.filter(pk=version_uuid)
            n_reports = 1
        elif linked_id and linked_id != 'na':
            reports = Report.objects.filter(linked_id=linked_id)
            n_reports = 1
        else:
            reports = Report.objects.non_deleted().filter(hide=False, identification_task__isnull=False).order_by('-server_upload_time')
            n_reports = len(reports)

        paginator = Paginator(reports, int(reports_per_page))
        page_num = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_num)

        reports_per_page_choices = range(0, min(1000, n_reports)+1, 25)

        context = {
            'reports': page_obj,
            'version_uuid': version_uuid,
            'reports_per_page_choices': reports_per_page_choices,
            'objects': page_obj,
            'pages': range(1, paginator.num_pages+1)
        }

        return render(request, 'tigacrafting/expert_report_status.html', context)
    else:
        return HttpResponseRedirect(reverse('login'))


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
            breeding_site_type=Report.BREEDING_SITE_TYPE_STORM_DRAIN
        )
    elif type == 'site-o':
        type_readable = "Breeding sites - Other"
        reports_qs = reports_qs.filter(
            type=Report.TYPE_SITE
        ).exclude(
            breeding_site_type=Report.BREEDING_SITE_TYPE_STORM_DRAIN
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
        reports_qs = reports_qs.filter(ia_filter_1__lte=float(aithr))

    reports_qs = reports_qs.prefetch_related('photos').select_related('country').order_by('-server_upload_time')
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

@api_view(['GET'])
def metadataPhoto(request):
    idReport = request.QUERY_PARAMS.get('id', None)
    idPhoto = request.QUERY_PARAMS.get('id_photo', None)
    utf8string = idReport.encode("utf-8")
    idPhotoUTF8 = idPhoto.encode("utf-8")
    photoData = []
    photoCoord = []
    photoDateTime = []
    exifgpsInfoDict = {}
    exifDateTime = {}
    gpsData = {}
    photo = Photo.objects.filter(report=utf8string).filter(id=idPhotoUTF8)
    for t in photo:
        urlPhoto = t.photo.url

    urlPhoto = BASE_DIR + urlPhoto

    exif = get_exif(urlPhoto)


    if exif is None:
        context = {'noData': 'No data available.'}
    else:
        if 'GPSInfo' in exif:
            _TAGS_r = dict(((v, k) for k, v in TAGS.items()))
            _GPSTAGS_r = dict(((v, k) for k, v in GPSTAGS.items()))

            exifgpsInfo = exif["GPSInfo"]
            for k in exifgpsInfo.keys():
                exifgpsInfoDict[str(GPSTAGS[k])] = exifgpsInfo[k]
                gpsData[str(GPSTAGS[k])] = str(exifgpsInfo[k])
            lat, lon = get_decimal_coordinates(exifgpsInfoDict)

            # lat, lon = get_decimal_coordinates(exif['GPSInfo'])
            photoCoord.append({'lat': lat, 'lon': lon})
            #gpsData.append({'gpsData': exifgpsInfoDict})

            del exif["GPSInfo"]

        if 'DateTime' in exif.keys():
            # for d in exif:
                # exifDateTime[str(TAGS[d])] = exif[d]
            photoDateTime.append({'DateTime': exif['DateTime']})

        if not photoCoord and not photoDateTime:
            context = {'photoData': exif}
        elif not photoDateTime:
            context = {'photoData': exif, 'photoCoord': photoCoord}
        elif not photoCoord:
            context = {'photoData': exif, 'photoDateTime': photoDateTime}
        else:
            context = {'photoData': exif, 'photoDateTime': photoDateTime, 'photoCoord': photoCoord}

    return Response(context)


def get_decimal_coordinates(info):
    try:
        for key in ['Latitude', 'Longitude']:
            v1 = str('GPS' + key)
            v2 = str('GPS' + key + 'Ref')

            if v1 in info.keys() and v2 in info.keys():
                e = info['GPS' + key]
                ref = info['GPS' + key + 'Ref']
                info[v1] = (Decimal(e[0][0] / e[0][1]) + Decimal(e[1][0] / e[1][1]) / 60 + Decimal(e[2][0] / e[2][1]) / 3600) * (-1 if ref in ['S', 'W'] else 1)
        if 'GPSLatitude' in info and 'GPSLongitude' in info:
            return [float(info['GPSLatitude']), float(info['GPSLongitude'])]
        else:
            return [0.0, 0.0]
    except:
        return None


def get_exif(filename):
    try:
        img = PIL.Image.open(filename)

        if img is not None:
            exif = {
                PIL.ExifTags.TAGS[key]: value
                for key, value in img._getexif().items()
                if key in PIL.ExifTags.TAGS or key in PIL.ExifTags.GPSTAGS
            }
        return exif
    except:
        return None
