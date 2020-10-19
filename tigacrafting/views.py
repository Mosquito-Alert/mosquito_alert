# coding=utf-8
from pydoc import visiblename
from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
import requests
import json

from rest_framework.decorators import api_view

from tigacrafting.models import *
from tigaserver_app.models import Photo, Report, ReportResponse
import dateutil.parser
from django.db.models import Count
import pytz
from datetime import datetime, date
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
from django.template.loader import render_to_string
from django.forms.models import modelformset_factory
from tigacrafting.forms import AnnotationForm, MovelabAnnotationForm, ExpertReportAnnotationForm, SuperExpertReportAnnotationForm, PhotoGrid
from tigaserver_app.models import Notification, NotificationContent, TigaUser, EuropeCountry
from zipfile import ZipFile
from io import BytesIO
from operator import attrgetter
from django.db.models import Q
from django.contrib.auth.models import User, Group
import urllib
import django.utils.html
from django.db import connection
from itertools import chain
from tigacrafting.messaging import send_message_android,send_message_ios
from tigaserver_app.serializers import custom_render_notification
from django.contrib.gis.geos import GEOSGeometry
from django.db import transaction
from tigacrafting.forms import LicenseAgreementForm
import logging
from common.translation import get_translation_in, get_locale_for_en
import html.entities
from django.template.loader import TemplateDoesNotExist
from django.utils.translation import gettext as _

#----------Metadades fotos----------#

import PIL.Image
from PIL.ExifTags import TAGS, GPSTAGS
from decimal import *
from tigaserver_project.settings import *
from rest_framework.response import Response
import re

#-----------------------------------#

logger_report_assignment = logging.getLogger('mosquitoalert.report.assignment')

def get_current_domain(request):
    if request.META['HTTP_HOST'] != '':
        return request.META['HTTP_HOST']
    if settings.DEBUG:
        current_domain = 'humboldt.ceab.csic.es'
    else:
        current_domain = 'tigaserver.atrapaeltigre.com'
    return current_domain


def photos_to_tasks():
    these_photos = Photo.objects.filter(crowdcraftingtask=None).exclude(report__hide=True).exclude(hide=True)
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
    tasks_filtered = filter(lambda x: not x.photo.report.deleted and x.photo.report.latest_version, tasks)
    return tasks_filtered


def filter_false_validated(reports, sort=True):
    if sort:
        reports_filtered = sorted(filter(lambda x: not x.deleted and x.latest_version and x.is_validated_by_two_experts_and_superexpert, reports),key=attrgetter('n_annotations'), reverse=True)
    else:
        reports_filtered = filter(lambda x: (not x.deleted) and x.latest_version and x.is_validated_by_two_experts_and_superexpert, reports)
    return reports_filtered

def fast_filter_reports(reports):
    #these are all the report_id in reports, with its max version number and the number of versions
    #the values at the end drops everything into a dictionary
    keys = Report.objects.exclude(creation_time__year=2014).filter(type='adult').values('report_id').annotate(Max('version_number')).annotate(Min('version_number')).annotate(Count('version_number'))
    report_id_table = {}
    for row in keys:
        report_id_table[row['report_id']] = {'max_version':row['version_number__max'],'min_version':row['version_number__min'],'num_versions': row['version_number__count']}
    reports_filtered = filter( lambda x: report_id_table[x.report_id]['num_versions'] == 1 or (report_id_table[x.report_id]['min_version'] != -1 and x.version_number == report_id_table[x.report_id]['max_version']), reports )
    return reports_filtered


def filter_reports(reports, sort=True):
    if sort:
        reports_filtered = sorted(filter(lambda x: not x.deleted and x.latest_version, reports), key=attrgetter('n_annotations'), reverse=True)
    else:
        reports_filtered = filter(lambda x: not x.deleted and x.latest_version, reports)
    return reports_filtered


def filter_spain_reports(reports, sort=True):
    if sort:
        reports_filtered = sorted( filter(lambda x: x.is_spain_p, reports), key=attrgetter('n_annotations'), reverse=True)
    else:
        reports_filtered = filter(lambda x: x.is_spain_p, reports)
    return reports_filtered


def filter_eu_reports(reports, sort=True):
    if sort:
        reports_filtered = sorted(filter(lambda x: not x.is_spain_p, reports), key=attrgetter('n_annotations'), reverse=True)
    else:
        reports_filtered = filter(lambda x: not x.is_spain_p, reports)
    return reports_filtered


def filter_reports_for_superexpert(reports):
    reports_filtered = filter(lambda x: not x.deleted and x.latest_version and len(list(filter(lambda y: y.is_expert() and y.validation_complete, x.expert_report_annotations.all()))) >= 3, reports)
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


BCN_BB = {'min_lat': 41.321049, 'min_lon': 2.052380, 'max_lat': 41.468609, 'max_lon': 2.225610}

ITALY_GEOMETRY = GEOSGeometry('{"type": "Polygon","coordinates": [[[7.250976562499999,43.70759350405294],[8.96484375,44.071800467511565],[10.96435546875,41.95131994679697],[7.822265625000001,41.0130657870063],[8.1298828125,38.788345355085625],[11.865234375,37.735969208590504],[14.1064453125,36.70365959719456],[14.985351562499998,36.31512514748051],[18.80859375,40.27952566881291],[12.45849609375,44.5278427984555],[13.86474609375,45.413876460821086],[14.04052734375,46.51351558059737],[12.238769531249998,47.264320080254805],[6.8994140625,46.10370875598026],[6.43798828125,45.120052841530544],[7.250976562499999,43.70759350405294]]]}')


def autoflag_others(id_annotation_report):
    this_annotation = ExpertReportAnnotation.objects.get(id=id_annotation_report)
    the_report = this_annotation.report
    annotations = ExpertReportAnnotation.objects.filter(report_id=the_report.version_UUID).filter(user__groups__name='expert')
    for anno in annotations:
        if anno.id != id_annotation_report:
            anno.status = 0
            anno.save()


def must_be_autoflagged(this_annotation, is_current_validated):
    if this_annotation is not None:
        the_report = this_annotation.report
        if the_report is not None:
            annotations = ExpertReportAnnotation.objects.filter(report_id=the_report.version_UUID,user__groups__name='expert',validation_complete=True).exclude(id=this_annotation.id)
            anno_count = 0
            classifications = []
            for anno in annotations:
                item = anno.category if anno.complex is None else anno.complex
                classifications.append(item)
                anno_count += 1
            this_annotation_item = this_annotation.category if this_annotation.complex is None else this_annotation.complex
            classifications.append(this_annotation_item)
            if is_current_validated and len(classifications) == 3 and ( len(set(classifications)) == len(classifications) ):
                return True
    return False
    '''
    if this_annotation is not None:
        the_report = this_annotation.report
        if the_report is not None:
            annotations = ExpertReportAnnotation.objects.filter(report_id=the_report.version_UUID, user__groups__name='expert').exclude(id=this_annotation.id)
            anno_count = 0
            one_positive_albopictus = False
            one_positive_aegypti = False
            one_unclassified_or_inconclusive = False
            for anno in annotations:
                validated = anno.validation_complete
                if anno.tiger_certainty_category is not None and anno.tiger_certainty_category > 0 and validated == True:
                    one_positive_albopictus = True
                if anno.aegypti_certainty_category is not None and anno.aegypti_certainty_category > 0 and validated == True:
                    one_positive_aegypti = True
                if anno.aegypti_certainty_category is not None and anno.aegypti_certainty_category <= 0 \
                        and anno.tiger_certainty_category is not None and anno.tiger_certainty_category <= 0 \
                        and validated == True:
                    one_unclassified_or_inconclusive = True
                if anno.aegypti_certainty_category is None and anno.tiger_certainty_category is None and validated == True:
                    one_unclassified_or_inconclusive = True
                anno_count += 1
            validated = is_current_validated
            if this_annotation.tiger_certainty_category is not None and this_annotation.tiger_certainty_category > 0 and validated == True:
                one_positive_albopictus = True
            if this_annotation.aegypti_certainty_category is not None and this_annotation.aegypti_certainty_category > 0 and validated == True:
                one_positive_aegypti = True
            if this_annotation.aegypti_certainty_category is not None and this_annotation.aegypti_certainty_category <= 0 \
                    and this_annotation.tiger_certainty_category is not None and this_annotation.tiger_certainty_category <= 0 \
                    and validated == True:
                one_unclassified_or_inconclusive = True
            if this_annotation.aegypti_certainty_category is None and this_annotation.tiger_certainty_category is None and validated == True:
                one_unclassified_or_inconclusive = True

            if one_positive_albopictus and one_positive_aegypti and one_unclassified_or_inconclusive and (anno_count + 1) == 3:
                return True
    return False
    '''

def get_sigte_map_info(report):
    cursor = connection.cursor()
    cursor.execute("SELECT id,lon,lat,private_webmap_layer FROM map_aux_reports WHERE version_uuid = %s", [report.version_UUID])
    row = cursor.fetchone()
    return row

def get_sigte_report_link(report,locale,current_domain):
    data = get_sigte_map_info(report)
    if data:
        lat = data[2]
        lon = data[1]
        id = data[0]
        url_template = "http://{0}/static/tigapublic/spain.html#/{1}/19/{2}/{3}/A,B,C,D/all/all/{4}".format(current_domain, locale, lat, lon, id)
        return url_template
    return None

# This can be called from outside the server, so we need current_domain for absolute urls
def issue_notification(report_annotation,current_domain):
    notification_content = NotificationContent()
    context_es = {}
    context_ca = {}
    context_en = {}
    locale_for_en = get_locale_for_en(report_annotation.report)

    notification_content.title_es = "¡Tu foto ha sido validada por un experto!"
    notification_content.title_ca = "La teva foto ha estat validada per un expert!"
    title_en = _("your_picture_has_been_validated_by_an_expert")
    notification_content.title_en = get_translation_in("your_picture_has_been_validated_by_an_expert", locale_for_en)

    if report_annotation.report.get_final_photo_url_for_notification():
        context_es['picture_link'] = 'http://' + current_domain + report_annotation.report.get_final_photo_url_for_notification()
        context_en['picture_link'] = 'http://' + current_domain + report_annotation.report.get_final_photo_url_for_notification()
        context_ca['picture_link'] = 'http://' + current_domain + report_annotation.report.get_final_photo_url_for_notification()

    if report_annotation.edited_user_notes:
        #clean_annotation = django.utils.html.escape(report_annotation.edited_user_notes)
        #clean_annotation = report_annotation.edited_user_notes.encode('ascii', 'xmlcharrefreplace').decode('utf-8')
        clean_annotation = report_annotation.edited_user_notes
        context_es['expert_note'] = clean_annotation
        context_en['expert_note'] = clean_annotation
        context_ca['expert_note'] = clean_annotation

    if report_annotation.message_for_user:
        #clean_annotation = django.utils.html.escape(report_annotation.message_for_user)
        #clean_annotation = report_annotation.message_for_user.encode('ascii', 'xmlcharrefreplace').decode('utf-8')
        clean_annotation = report_annotation.message_for_user
        context_es['message_for_user'] = clean_annotation
        context_en['message_for_user'] = clean_annotation
        context_ca['message_for_user'] = clean_annotation

    if report_annotation.report:
        clean_annotation = django.utils.html.escape(report_annotation.report.get_final_combined_expert_category_public_map_euro('es'))
        clean_annotation = clean_annotation.encode('ascii', 'xmlcharrefreplace').decode('utf-8')
        context_es['validation_category'] = clean_annotation
        clean_annotation = django.utils.html.escape(report_annotation.report.get_final_combined_expert_category_public_map_euro(locale_for_en))
        clean_annotation = clean_annotation.encode('ascii', 'xmlcharrefreplace').decode('utf-8')
        context_en['validation_category'] = clean_annotation
        clean_annotation = django.utils.html.escape(report_annotation.report.get_final_combined_expert_category_public_map_euro('ca'))
        clean_annotation = clean_annotation.encode('ascii', 'xmlcharrefreplace').decode('utf-8')
        context_ca['validation_category'] = clean_annotation
        map_data = get_sigte_map_info(report_annotation.report)

        if map_data:
            context_es['map_link'] = get_sigte_report_link(report_annotation.report, "es", current_domain)
            context_en['map_link'] = get_sigte_report_link(report_annotation.report, "en", current_domain)
            context_ca['map_link'] = get_sigte_report_link(report_annotation.report, "ca", current_domain)

    notification_content.body_html_es = render_to_string('tigacrafting/validation_message_template_es.html', context_es).replace('&amp;', '&')
    notification_content.body_html_ca = render_to_string('tigacrafting/validation_message_template_ca.html', context_ca).replace('&amp;', '&')

    try:
        notification_content.body_html_en = render_to_string('tigacrafting/validation_message_template_' + locale_for_en + '.html', context_en).replace('&amp;', '&')
    except TemplateDoesNotExist:
        notification_content.body_html_en = render_to_string('tigacrafting/validation_message_template_en.html', context_en).replace('&amp;', '&')

    notification_content.save()
    notification = Notification(report=report_annotation.report, user=report_annotation.report.user, expert=report_annotation.user, notification_content=notification_content)
    notification.save()

    recipient = report_annotation.report.user
    if recipient.device_token is not None and recipient.device_token != '':
        if (recipient.user_UUID.islower()):
            json_notif = custom_render_notification(notification, 'es')
            try:
                send_message_android(recipient.device_token, notification_content.title_es, '', json_notif)
            except Exception as e:
                pass
        else:
            try:
                send_message_ios(recipient.device_token, notification_content.title_es, '')
            except Exception as e:
                pass
    '''
    About to deploy epi data, let's put this in the fridge for now
    # if there is a similar notification issued for this user recently
    if not notification_already_issued(report_annotation.report, report_annotation.report.user, report_annotation.user, notification_content.title_es):
        notification.save()
        recipient = report_annotation.report.user
        if recipient.device_token is not None and recipient.device_token != '':
            if (recipient.user_UUID.islower()):
                json_notif = custom_render_notification(notification, 'es')
                try:
                    send_message_android(recipient.device_token, notification_content.title_es, '', json_notif)
                except Exception as e:
                    pass
            else:
                try:
                    send_message_ios(recipient.device_token, notification_content.title_es, '')
                except Exception as e:
                    pass

    #checks if a notification about this report, sent to user_sent_to, from expert_sent_from has been sent
    #this will hopefully avoid multi-sent notifications
    def notification_already_issued(report, user_sent_to, expert_sent_from, title_es):
        return Notification.objects.filter(report=report,user=user_sent_to,expert=expert_sent_from,notification_content__title_es=title_es).exists()
    '''

def assign_reports_to_user(this_user, national_supervisor_ids, current_pending, country_with_supervisor_set, max_pending, max_given):
    """
    :param this_user: user to which the reports will be assigned
    :param national_supervisor_ids: list of national supervisor ids in dict format [{'user__id':id}...{}]
    :param current_pending: number of current pending reports for this_user
    :param country_with_supervisor_set: set of id_country which have supervisor
    :param max_pending: maximum number of pending reports per user
    :param max_given: number of users to which a report is given (excluding superexpert)
    """
    logger_report_assignment.debug('Begin ASSIGN REPORT for User {0}'.format(this_user,))
    logger_report_assignment.debug('Assigning reports to user {0}'.format(this_user, ))
    # dictionary or reports assigned to some supervisor
    report_assigned_to_supervisor = ExpertReportAnnotation.objects.filter(user__id__in=national_supervisor_ids).values('report').distinct()
    # set of these report ids
    report_assigned_to_supervisor_set = set([d['report'] for d in report_assigned_to_supervisor])
    this_user_is_team_bcn = this_user.groups.filter(name='team_bcn').exists()
    this_user_is_team_not_bcn = this_user.groups.filter(name='team_not_bcn').exists()
    this_user_is_supervisor = this_user.userstat.is_national_supervisor()
    this_user_is_europe = this_user.groups.filter(name='eu_group_europe').exists()
    #this_user_is_spain = this_user.groups.filter(name='eu_group_spain').exists()
    this_user_is_spain = not this_user_is_europe

    my_reports = ExpertReportAnnotation.objects.filter(user=this_user).filter(report__type='adult').values('report').distinct()
    if current_pending < max_pending:
        logger_report_assignment.debug('User {0} has less than {1} reports assigned (currently {2})'.format(this_user, max_pending, current_pending))
        n_to_get = max_pending - current_pending
        logger_report_assignment.debug('User {0} trying to get {1} reports'.format(this_user, n_to_get))
        new_reports_unfiltered = Report.objects.exclude(creation_time__year=2014).exclude(note__icontains="#345").exclude(version_UUID__in=my_reports).exclude(photos__isnull=True).exclude(hide=True).filter(type='adult').annotate(n_annotations=Count('expert_report_annotations')).filter(n_annotations__lt=max_given)
        '''
        if new_reports_unfiltered and this_user_is_team_bcn:
            new_reports_unfiltered = new_reports_unfiltered.filter(Q(location_choice='selected', selected_location_lon__range=(BCN_BB['min_lon'], BCN_BB['max_lon']),selected_location_lat__range=(BCN_BB['min_lat'], BCN_BB['max_lat'])) | Q(location_choice='current',current_location_lon__range=(BCN_BB['min_lon'],BCN_BB['max_lon']),current_location_lat__range=(BCN_BB['min_lat'],BCN_BB['max_lat'])))
        if new_reports_unfiltered and this_user_is_team_not_bcn:
            new_reports_unfiltered = new_reports_unfiltered.exclude(Q(location_choice='selected', selected_location_lon__range=(BCN_BB['min_lon'], BCN_BB['max_lon']), selected_location_lat__range=(BCN_BB['min_lat'], BCN_BB['max_lat'])) | Q(location_choice='current', current_location_lon__range=(BCN_BB['min_lon'],BCN_BB['max_lon']),current_location_lat__range=(BCN_BB['min_lat'],BCN_BB['max_lat'])))
        '''
        if this_user_is_supervisor:
            #logger_report_assignment.debug('User {0} is supervisor'.format(this_user,))
            reports_supervised_country = new_reports_unfiltered.filter(country__gid=this_user.userstat.national_supervisor_of.gid)
            # list of countries with supervisor (excluding present)
            country_with_supervisor_other_than_this = UserStat.objects.filter(national_supervisor_of__isnull=False).exclude(national_supervisor_of__gid=this_user.userstat.national_supervisor_of.gid).values('national_supervisor_of__gid').distinct()
            # list of reports with supervisor and two annotations -> these reports are meant for the supervisor and should not be assigned
            reports_other_supervised_country_expecting_supervisor = Report.objects.exclude(creation_time__year=2014).exclude(note__icontains="#345").exclude(version_UUID__in=my_reports).exclude(photos__isnull=True).exclude(hide=True).filter(type='adult').annotate(n_annotations=Count('expert_report_annotations')).filter(n_annotations=2).filter(country__gid__in=country_with_supervisor_other_than_this)
            # so we remove them from the available reports for this expert
            reports_non_supervised_country = new_reports_unfiltered.exclude(version_UUID__in=reports_supervised_country.values('version_UUID')).exclude(version_UUID__in=reports_other_supervised_country_expecting_supervisor.values('version_UUID'))
            reports_supervised_country_filtered = filter_reports(reports_supervised_country.order_by('creation_time'))
            reports_non_supervised_country_filtered = filter_reports(reports_non_supervised_country.order_by('creation_time'))
            new_filtered_reports = reports_supervised_country_filtered + reports_non_supervised_country_filtered
        else:
            #logger_report_assignment.debug('User {0} is not supervisor'.format(this_user, ))
            country_with_supervisor = UserStat.objects.filter(national_supervisor_of__isnull=False).values('national_supervisor_of__gid').distinct()
            # these are the reports in supervised countries, already assigned to two experts, so they should be assigned to supervisor and no one else
            reports_other_supervised_country_expecting_supervisor = Report.objects.exclude(creation_time__year=2014).exclude(note__icontains="#345").exclude(version_UUID__in=my_reports).exclude(hide=True).exclude(photos__isnull=True).filter(type='adult').annotate(n_annotations=Count('expert_report_annotations')).filter(n_annotations=2).filter(country__gid__in=country_with_supervisor)
            # we put the countries with supervisor first on the list. This aims to reduce the amount of time the regional supervisor has to wait to be assigned last report
            # we EXCLUDE the reports_other_supervised_country_expecting_supervisor from both lists -- these are reserved reports for the supervisor
            reports_in_any_country_with_supervisor = new_reports_unfiltered.filter(country__gid__in=country_with_supervisor).exclude(version_UUID__in=reports_other_supervised_country_expecting_supervisor.values('version_UUID'))
            reports_in_country_without_supervisor = new_reports_unfiltered.exclude(country__gid__in=country_with_supervisor).exclude(version_UUID__in=reports_other_supervised_country_expecting_supervisor.values('version_UUID'))
            reports_in_any_country_with_supervisor_filtered = filter_reports(reports_in_any_country_with_supervisor.order_by('creation_time'))
            reports_in_country_without_supervisor_filtered = filter_reports(reports_in_country_without_supervisor.order_by('creation_time'))
            new_filtered_reports = reports_in_any_country_with_supervisor_filtered + reports_in_country_without_supervisor_filtered
        logger_report_assignment.debug('User {0} has {1} potentially assignable reports'.format(this_user, len(new_filtered_reports)))

        if this_user_is_spain:
            logger_report_assignment.debug('User {0} is in spanish group'.format(this_user, ))
            new_reports = filter_spain_reports(new_filtered_reports)
            logger_report_assignment.debug('User {0} has {1} of {2} reports located in Spain/Other area'.format(this_user, len(new_reports), len(new_filtered_reports), ))
        elif this_user_is_europe:
            logger_report_assignment.debug('User {0} is in european group'.format(this_user, ))
            new_reports = filter_eu_reports(new_filtered_reports)
            logger_report_assignment.debug('User {0} has {1} of {2} reports located in Europe area'.format(this_user, len(new_reports),len(new_filtered_reports), ))
        else:
            new_reports = new_filtered_reports

        grabbed_reports = -1
        reports_taken = 0
        logger_report_assignment.debug('Looping reports for User {0}'.format(this_user,))
        for this_report in new_reports:
            new_annotation = ExpertReportAnnotation(report=this_report, user=this_user)
            who_has_count = this_report.get_who_has_count()
            logger_report_assignment.debug('Report {0} assigned to {1} people'.format(this_report, who_has_count, ))
            if this_user_is_supervisor:
                logger_report_assignment.debug('User {0} is supervisor for {1}'.format(this_user, this_user.userstat.national_supervisor_of.name_engl))
                if this_user.userstat.is_national_supervisor_for_country(this_report.country):
                    logger_report_assignment.debug('User {0} is supervisor for country of report {1} which is {2}'.format(this_user, this_report, this_report.country, ))
                    if who_has_count == 2:
                        logger_report_assignment.debug('Assigning full report {0} to supervisor User {1} because it has been assigned to 2 other users'.format(this_report, this_user,))
                        new_annotation.simplified_annotation = False
                        grabbed_reports += 1
                        reports_taken += 1
                        new_annotation.save()
                    else:
                        logger_report_assignment.debug('NOT assigning report to supervisor User {0} because it has not yet been assigned to 2 other users (assigned to {1} other users)'.format(this_user, who_has_count,))
                else:
                    logger_report_assignment.debug('User {0} is NOT supervisor for country of report {1} which is {2}'.format(this_user, this_report,this_report.country, ))
                    logger_report_assignment.debug('Assigning report {0} to supervisor User {1} because it is available'.format(this_report, this_user, ))
                    if who_has_count == 0 or who_has_count == 1:
                        logger_report_assignment.debug('Report assigned to supervisor User {0} as simplified'.format(this_user, ))
                        new_annotation.simplified_annotation = True
                    else:
                        logger_report_assignment.debug('Report assigned to supervisor User {0} as extended'.format(this_user, ))
                    grabbed_reports += 1
                    reports_taken += 1
                    new_annotation.save()
            else:
                logger_report_assignment.debug('User {0} is NOT supervisor'.format(this_user, ))
                if this_report.country is None:
                    logger_report_assignment.debug('Report {0} has no country'.format(this_report, ))
                    if who_has_count == 0 or who_has_count == 1:
                        logger_report_assignment.debug('Report assigned to normal User {0} as simplified'.format(this_user, ))
                        new_annotation.simplified_annotation = True
                    else:
                        logger_report_assignment.debug('Report assigned to normal User {0} as extended'.format(this_user, ))
                        new_annotation.simplified_annotation = False
                    grabbed_reports += 1
                    reports_taken += 1
                    new_annotation.save()
                else:
                    logger_report_assignment.debug('Report {0} is in country {1}'.format(this_report, this_report.country))
                    if this_report.country.gid in country_with_supervisor_set:
                        logger_report_assignment.debug('Report {0} is in country {1} which has a supervisor'.format(this_report, this_report.country))
                        #Assign only if only 1 other user or nobody is assigned
                        if who_has_count <= 1:
                            logger_report_assignment.debug('Report {0} is assigned to less or equal than 1 people ({1})'.format(this_report, who_has_count))
                            #if this_report.version_UUID in report_assigned_to_supervisor_set:
                            if who_has_count == 0 or who_has_count == 1:
                                logger_report_assignment.debug('Report assigned to normal User {0} as simplified'.format(this_user, ))
                                new_annotation.simplified_annotation = True
                            else:
                                logger_report_assignment.debug('Report assigned to normal User {0} as extended'.format(this_user, ))
                                new_annotation.simplified_annotation = False
                            grabbed_reports += 1
                            reports_taken += 1
                            new_annotation.save()
                            #else:
                                #logger_report_assignment.debug('Report {0} not yet assigned to supervisor, not assigning'.format(this_report, ))
                    else:
                        logger_report_assignment.debug('Report {0} is in country {1} which has NO supervisor'.format(this_report,this_report.country))
                        if who_has_count == 0 or who_has_count == 1:
                            logger_report_assignment.debug('Report assigned to normal User {0} as simplified'.format(this_user, ))
                            new_annotation.simplified_annotation = True
                        else:
                            logger_report_assignment.debug('Report assigned to normal User {0} as extended'.format(this_user, ))
                            new_annotation.simplified_annotation = False
                        grabbed_reports += 1
                        reports_taken += 1
                        new_annotation.save()
            if reports_taken == n_to_get:
                break
        this_user.userstat.grabbed_reports = grabbed_reports
        this_user.userstat.save()
        logger_report_assignment.debug('End ASSIGN REPORT for User {0}'.format(this_user, ))
        logger_report_assignment.debug(' ')


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


@transaction.atomic
@login_required
def expert_report_annotation(request, scroll_position='', tasks_per_page='10', note_language='es', load_new_reports='F', year='all', orderby='date', tiger_certainty='all', site_certainty='all', pending='na', checked='na', status='all', final_status='na', max_pending=5, max_given=3, version_uuid='na', linked_id='na', edit_mode='off', tags_filter='na',loc='na'):
    this_user = request.user
    if getattr(settings, 'SHOW_USER_AGREEMENT_ENTOLAB', False) == True:
        if this_user.userstat:
            if not this_user.userstat.has_accepted_license():
                return HttpResponseRedirect(reverse('entolab_license_agreement'))
        else:
            return HttpResponse("There is a problem with your current user. Please contact the EntoLab admin at " + settings.ENTOLAB_ADMIN)
    current_domain = get_current_domain(request)
    this_user_is_expert = this_user.groups.filter(name='expert').exists()
    this_user_is_superexpert = this_user.groups.filter(name='superexpert').exists()
    this_user_is_team_bcn = this_user.groups.filter(name='team_bcn').exists()
    this_user_is_team_not_bcn = this_user.groups.filter(name='team_not_bcn').exists()
    #this_user_is_team_italy = this_user.groups.filter(name='team_italy').exists()
    #this_user_is_team_not_italy = this_user.groups.filter(name='team_not_italy').exists()
    this_user_is_reritja = (this_user.id == 25)

    if this_user_is_expert or this_user_is_superexpert:
        args = {}
        args.update(csrf(request))
        args['scroll_position'] = scroll_position
        if this_user_is_superexpert:
            AnnotationFormset = modelformset_factory(ExpertReportAnnotation, form=SuperExpertReportAnnotationForm, extra=0)
        else:
            AnnotationFormset = modelformset_factory(ExpertReportAnnotation, form=ExpertReportAnnotationForm, extra=0)
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
            tags_filter = request.POST.get('tags_filter', tags_filter)
            checked = request.POST.get('checked', checked)
            loc = request.POST.get('loc', loc)
            tasks_per_page = request.POST.get('tasks_per_page', tasks_per_page)
            note_language = request.GET.get('note_language', "es")
            load_new_reports = request.POST.get('load_new_reports', load_new_reports)
            save_formset = request.POST.get('save_formset', "F")
            if save_formset == "T":
                formset = AnnotationFormset(request.POST)
                if formset.is_valid():
                    for f in formset:
                        one_form = f.save(commit=False)
                        auto_flag = must_be_autoflagged(one_form,one_form.validation_complete)
                        if auto_flag:
                            one_form.status = 0
                        if(this_user_is_reritja and one_form.validation_complete == True):
                            issue_notification(one_form,current_domain)
                        one_form.save()
                        f.save_m2m()
                        if auto_flag:
                            autoflag_others(one_form.id)
                else:
                    return render(request, 'tigacrafting/formset_errors.html', {'formset': formset})
            page = request.POST.get('page')
            if not page:
                page = '1'
            return HttpResponseRedirect(reverse('expert_report_annotation') + '?page='+page+'&tasks_per_page='+tasks_per_page+'&note_language=' + note_language + '&loc=' + loc + '&scroll_position='+scroll_position+(('&pending='+pending) if pending else '') + (('&checked='+checked) if checked else '') + (('&final_status='+final_status) if final_status else '') + (('&version_uuid='+version_uuid) if version_uuid else '') + (('&linked_id='+linked_id) if linked_id else '') + (('&orderby='+orderby) if orderby else '') + (('&tiger_certainty='+tiger_certainty) if tiger_certainty else '') + (('&site_certainty='+site_certainty) if site_certainty else '') + (('&status='+status) if status else '') + (('&load_new_reports='+load_new_reports) if load_new_reports else '') + (('&tags_filter=' + urllib.parse.quote_plus(tags_filter)) if tags_filter else ''))
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
            tags_filter = request.GET.get('tags_filter', tags_filter)
            checked = request.GET.get('checked', checked)
            loc = request.GET.get('loc', loc)
            load_new_reports = request.GET.get('load_new_reports', load_new_reports)
            edit_mode = request.GET.get('edit_mode', edit_mode)

        #current_pending = ExpertReportAnnotation.objects.filter(user=this_user).filter(validation_complete=False).count()
        current_pending = ExpertReportAnnotation.objects.filter(user=this_user).filter(validation_complete=False).filter(report__type='adult').count()
        #my_reports = ExpertReportAnnotation.objects.filter(user=this_user).values('report')
        my_reports = ExpertReportAnnotation.objects.filter(user=this_user).filter(report__type='adult').values('report').distinct()

        '''
        if loc == 'spain':
            all_annotations = all_annotations.filter(Q(report__country__isnull=True) | Q(report__country__gid=17))
        elif loc == 'europe':
            all_annotations = all_annotations.filter(Q(report__country__isnull=False) & ~Q(report__country__gid=17))
        else:
            pass
        '''

        if loc == 'spain':
            hidden_final_reports_superexpert = set(ExpertReportAnnotation.objects.filter(user__groups__name='superexpert', validation_complete=True,revise=True, status=-1).filter(Q(report__country__isnull=True) | Q(report__country__gid=17)).values_list('report', flat=True))
            flagged_final_reports_superexpert = set(ExpertReportAnnotation.objects.filter(user__groups__name='superexpert', validation_complete=True,revise=True, status=0).filter(Q(report__country__isnull=True) | Q(report__country__gid=17)).exclude(report__version_UUID__in=hidden_final_reports_superexpert).values_list('report', flat=True))
            public_final_reports_superexpert = set(ExpertReportAnnotation.objects.filter(user__groups__name='superexpert', validation_complete=True,revise=True, status=1).filter(Q(report__country__isnull=True) | Q(report__country__gid=17)).exclude(report__version_UUID__in=hidden_final_reports_superexpert).exclude(report__version_UUID__in=flagged_final_reports_superexpert).values_list('report', flat=True))
            hidden_final_reports_expert = set(ExpertReportAnnotation.objects.filter(user__groups__name='expert', validation_complete=True, status=-1).exclude(report__version_UUID__in=public_final_reports_superexpert).exclude(report__version_UUID__in=flagged_final_reports_superexpert).filter(Q(report__country__isnull=True) | Q(report__country__gid=17)).values_list('report', flat=True))
            flagged_final_reports_expert = set(ExpertReportAnnotation.objects.filter(user__groups__name='expert', validation_complete=True, status=0).exclude(report__version_UUID__in=public_final_reports_superexpert).exclude(report__version_UUID__in=hidden_final_reports_superexpert).filter(Q(report__country__isnull=True) | Q(report__country__gid=17)).values_list('report', flat=True))
            public_final_reports_expert = set(ExpertReportAnnotation.objects.filter(user__groups__name='expert', validation_complete=True, status=1).exclude(report__version_UUID__in=flagged_final_reports_superexpert).exclude(report__version_UUID__in=hidden_final_reports_superexpert).filter(Q(report__country__isnull=True) | Q(report__country__gid=17)).values_list('report', flat=True))
        elif loc == 'europe':
            hidden_final_reports_superexpert = set(ExpertReportAnnotation.objects.filter(user__groups__name='superexpert', validation_complete=True,revise=True, status=-1).filter(Q(report__country__isnull=False) & ~Q(report__country__gid=17)).values_list('report', flat=True))
            flagged_final_reports_superexpert = set(ExpertReportAnnotation.objects.filter(user__groups__name='superexpert', validation_complete=True,revise=True, status=0).filter(Q(report__country__isnull=False) & ~Q(report__country__gid=17)).exclude(report__version_UUID__in=hidden_final_reports_superexpert).values_list('report', flat=True))
            public_final_reports_superexpert = set(ExpertReportAnnotation.objects.filter(user__groups__name='superexpert', validation_complete=True,revise=True, status=1).filter(Q(report__country__isnull=False) & ~Q(report__country__gid=17)).exclude(report__version_UUID__in=hidden_final_reports_superexpert).exclude(report__version_UUID__in=flagged_final_reports_superexpert).values_list('report', flat=True))
            hidden_final_reports_expert = set(ExpertReportAnnotation.objects.filter(user__groups__name='expert', validation_complete=True,status=-1).exclude(report__version_UUID__in=public_final_reports_superexpert).exclude(report__version_UUID__in=flagged_final_reports_superexpert).filter(Q(report__country__isnull=False) & ~Q(report__country__gid=17)).values_list('report', flat=True))
            flagged_final_reports_expert = set(ExpertReportAnnotation.objects.filter(user__groups__name='expert', validation_complete=True,status=0).exclude(report__version_UUID__in=public_final_reports_superexpert).exclude(report__version_UUID__in=hidden_final_reports_superexpert).filter(Q(report__country__isnull=False) & ~Q(report__country__gid=17)).values_list('report', flat=True))
            public_final_reports_expert = set(ExpertReportAnnotation.objects.filter(user__groups__name='expert', validation_complete=True,status=1).exclude(report__version_UUID__in=flagged_final_reports_superexpert).exclude(report__version_UUID__in=hidden_final_reports_superexpert).filter(Q(report__country__isnull=False) & ~Q(report__country__gid=17)).values_list('report', flat=True))
        else:
            hidden_final_reports_superexpert = set(ExpertReportAnnotation.objects.filter(user__groups__name='superexpert', validation_complete=True,revise=True, status=-1).values_list('report', flat=True))
            flagged_final_reports_superexpert = set(ExpertReportAnnotation.objects.filter(user__groups__name='superexpert', validation_complete=True,revise=True, status=0).exclude(report__version_UUID__in=hidden_final_reports_superexpert).values_list('report', flat=True))
            public_final_reports_superexpert = set(ExpertReportAnnotation.objects.filter(user__groups__name='superexpert', validation_complete=True,revise=True, status=1).exclude(report__version_UUID__in=hidden_final_reports_superexpert).exclude(report__version_UUID__in=flagged_final_reports_superexpert).values_list('report', flat=True))
            hidden_final_reports_expert = set(ExpertReportAnnotation.objects.filter(user__groups__name='expert', validation_complete=True, status=-1).exclude(report__version_UUID__in=public_final_reports_superexpert).exclude(report__version_UUID__in=flagged_final_reports_superexpert).values_list('report', flat=True))
            flagged_final_reports_expert = set(ExpertReportAnnotation.objects.filter(user__groups__name='expert', validation_complete=True, status=0).exclude(report__version_UUID__in=public_final_reports_superexpert).exclude(report__version_UUID__in=hidden_final_reports_superexpert).values_list('report', flat=True))
            public_final_reports_expert = set(ExpertReportAnnotation.objects.filter(user__groups__name='expert', validation_complete=True, status=1).exclude(report__version_UUID__in=flagged_final_reports_superexpert).exclude(report__version_UUID__in=hidden_final_reports_superexpert).values_list('report', flat=True))

        hidden_final_reports = set(list(hidden_final_reports_superexpert) + list(hidden_final_reports_expert))
        flagged_final_reports = set(list(flagged_final_reports_superexpert) + list(flagged_final_reports_expert))
        public_final_reports = set(list(public_final_reports_superexpert) + list(public_final_reports_expert))

        if this_user_is_expert and load_new_reports == 'T':
            national_supervisor_ids = UserStat.objects.filter(national_supervisor_of__isnull=False).values('user__id').distinct()
            country_with_supervisor = UserStat.objects.filter(national_supervisor_of__isnull=False).values('national_supervisor_of__gid').distinct()
            country_with_supervisor_set = set([d['national_supervisor_of__gid'] for d in country_with_supervisor])
            assign_reports_to_user(this_user,national_supervisor_ids,current_pending,country_with_supervisor_set,max_pending,max_given)
            '''
            if current_pending < max_pending:
                n_to_get = max_pending - current_pending

                new_reports_unfiltered = Report.objects.exclude(creation_time__year=2014).exclude(note__icontains="#345").exclude(version_UUID__in=my_reports).exclude(hide=True).exclude(photos=None).filter(type='adult').annotate(n_annotations=Count('expert_report_annotations')).filter(n_annotations__lt=max_given)
                new_reports_unfiltered_and_false_validated = Report.objects.exclude(creation_time__year=2014).exclude(note__icontains="#345").exclude(version_UUID__in=my_reports).exclude(hide=True).exclude(photos=None).filter(type='adult').annotate(n_annotations=Count('expert_report_annotations')).filter(n_annotations__lt=max_given+1)
                
                if new_reports_unfiltered and this_user_is_team_bcn:
                    new_reports_unfiltered = new_reports_unfiltered.filter(Q(location_choice='selected', selected_location_lon__range=(BCN_BB['min_lon'],BCN_BB['max_lon']),selected_location_lat__range=(BCN_BB['min_lat'], BCN_BB['max_lat'])) | Q(location_choice='current', current_location_lon__range=(BCN_BB['min_lon'],BCN_BB['max_lon']), current_location_lat__range=(BCN_BB['min_lat'], BCN_BB['max_lat'])))
                if new_reports_unfiltered and this_user_is_team_not_bcn:
                    new_reports_unfiltered = new_reports_unfiltered.exclude(Q(location_choice='selected', selected_location_lon__range=(BCN_BB['min_lon'],BCN_BB['max_lon']),selected_location_lat__range=(BCN_BB['min_lat'], BCN_BB['max_lat'])) | Q(location_choice='current', current_location_lon__range=(BCN_BB['min_lon'],BCN_BB['max_lon']),current_location_lat__range=(BCN_BB['min_lat'], BCN_BB['max_lat'])))
                
                if new_reports_unfiltered:
                    new_filtered_reports = filter_reports(new_reports_unfiltered.order_by('creation_time'))
                    new_filtered_false_validated_reports = filter_false_validated(new_reports_unfiltered_and_false_validated.order_by('creation_time'))
                    new_reports = list(set(new_filtered_reports + new_filtered_false_validated_reports))
                    reports_to_take = new_reports[0:n_to_get]
                    user_stats = None
                    try:
                        user_stats = UserStat.objects.get(user_id=this_user.id)
                    except ObjectDoesNotExist:
                        pass
                    grabbed_reports = -1
                    if user_stats:
                        grabbed_reports = user_stats.grabbed_reports
                    for this_report in reports_to_take:
                        if not this_report.user_has_report(this_user):
                            new_annotation = ExpertReportAnnotation(report=this_report, user=this_user)
                            who_has_count = this_report.get_who_has_count()
                            if who_has_count == 0 or who_has_count == 1:
                                #No one has the report, is simplified
                                new_annotation.simplified_annotation = True
                            grabbed_reports += 1
                            new_annotation.save()
                    if grabbed_reports != -1 and user_stats:
                        user_stats.grabbed_reports = grabbed_reports
                        user_stats.save()
            '''
        elif this_user_is_superexpert:
            new_reports_unfiltered = Report.objects.exclude(creation_time__year=2014).exclude(creation_time__year=2015).exclude(note__icontains="#345").exclude(version_UUID__in=my_reports).exclude(hide=True).exclude(photos__isnull=True).filter(type='adult').annotate(n_annotations=Count('expert_report_annotations')).filter(n_annotations__gte=max_given)
            #new_reports_unfiltered = Report.objects.exclude(creation_time__year=2014).exclude(version_UUID__in=my_reports).exclude(hide=True).exclude(photos__isnull=True).filter(type='adult').annotate(n_annotations=Count('expert_report_annotations')).filter(n_annotations__gte=max_given)
            #new_reports_unfiltered = Report.objects.exclude(creation_time__year=2014).exclude(version_UUID__in=my_reports).exclude(hide=True).exclude(photos__isnull=True).filter(type__in=['adult', 'site']).annotate(n_annotations=Count('expert_report_annotations')).filter(n_annotations__gte=max_given)

            if new_reports_unfiltered and this_user_is_team_bcn:
                new_reports_unfiltered = new_reports_unfiltered.filter(Q(location_choice='selected', selected_location_lon__range=(BCN_BB['min_lon'],BCN_BB['max_lon']),selected_location_lat__range=(BCN_BB['min_lat'], BCN_BB['max_lat'])) | Q(location_choice='current', current_location_lon__range=(BCN_BB['min_lon'],BCN_BB['max_lon']),current_location_lat__range=(BCN_BB['min_lat'], BCN_BB['max_lat'])))
            if new_reports_unfiltered and this_user_is_team_not_bcn:
                new_reports_unfiltered = new_reports_unfiltered.exclude(Q(location_choice='selected', selected_location_lon__range=(BCN_BB['min_lon'],BCN_BB['max_lon']),selected_location_lat__range=(BCN_BB['min_lat'], BCN_BB['max_lat'])) | Q(location_choice='current', current_location_lon__range=(BCN_BB['min_lon'],BCN_BB['max_lon']),current_location_lat__range=(BCN_BB['min_lat'], BCN_BB['max_lat'])))
            #if new_reports_unfiltered and this_user_is_team_italy:
                #new_reports_unfiltered = new_reports_unfiltered.filter(point__within=ITALY_GEOMETRY)
            #if new_reports_unfiltered and this_user_is_team_not_italy:
                    #new_reports_unfiltered = new_reports_unfiltered.exclude(point__within=ITALY_GEOMETRY)
            if this_user.id == 25: #it's roger, don't assign reports from barcelona prior to 03/10/2017
                new_reports_unfiltered = new_reports_unfiltered.exclude(Q(Q(location_choice='selected', selected_location_lon__range=(BCN_BB['min_lon'], BCN_BB['max_lon']), selected_location_lat__range=(BCN_BB['min_lat'], BCN_BB['max_lat'])) | Q(location_choice='current', current_location_lon__range=(BCN_BB['min_lon'], BCN_BB['max_lon']),current_location_lat__range=(BCN_BB['min_lat'], BCN_BB['max_lat']))) & Q(creation_time__lte=date(2017, 3, 10)))
            if new_reports_unfiltered:
                new_reports = filter_reports_for_superexpert(new_reports_unfiltered)
                for this_report in new_reports:
                    new_annotation = ExpertReportAnnotation(report=this_report, user=this_user)
                    new_annotation.save()

        all_annotations = ExpertReportAnnotation.objects.filter(user=this_user).filter(report__type='adult')

        # if loc == 'spain':
        #     my_version_uuids = all_annotations.filter(Q(report__country__isnull=True) | Q(report__country__gid=17)).values('report__version_UUID').distinct()
        # elif loc == 'europe':
        #     my_version_uuids = all_annotations.filter(Q(report__country__isnull=False) & ~Q(report__country__gid=17)).values('report__version_UUID').distinct()
        # else:
        #     my_version_uuids = all_annotations.values('report__version_UUID').distinct()

        my_linked_ids = all_annotations.values('linked_id').distinct()
        if this_user_is_expert:
            if (version_uuid == 'na' and linked_id == 'na' and tags_filter == 'na') and (not pending or pending == 'na'):
                pending = 'pending'
        if this_user_is_superexpert:
            if (version_uuid == 'na' and linked_id == 'na' and tags_filter == 'na') and (not final_status or final_status == 'na'):
                final_status = 'public'
            if (version_uuid == 'na' and linked_id == 'na' and tags_filter == 'na') and (not checked or checked == 'na'):
                checked = 'unchecked'
            n_flagged = all_annotations.filter(report__in=flagged_final_reports).count()
            n_hidden = all_annotations.filter(report__in=hidden_final_reports).count()
            n_public = all_annotations.filter(report__in=public_final_reports).exclude(report__in=flagged_final_reports).exclude(report__in=hidden_final_reports).count()

            if loc == 'spain':
                n_unchecked = all_annotations.filter(Q(report__country__isnull=True) | Q(report__country__gid=17)).filter(validation_complete=False).count()
                n_confirmed = all_annotations.filter(Q(report__country__isnull=True) | Q(report__country__gid=17)).filter(validation_complete=True, revise=False).count()
                n_revised = all_annotations.filter(Q(report__country__isnull=True) | Q(report__country__gid=17)).filter(validation_complete=True, revise=True).count()
            elif loc == 'europe':
                n_unchecked = all_annotations.filter(Q(report__country__isnull=False) & ~Q(report__country__gid=17)).filter(validation_complete=False).count()
                n_confirmed = all_annotations.filter(Q(report__country__isnull=False) & ~Q(report__country__gid=17)).filter(validation_complete=True, revise=False).count()
                n_revised = all_annotations.filter(Q(report__country__isnull=False) & ~Q(report__country__gid=17)).filter(validation_complete=True, revise=True).count()
            else:
                n_unchecked = all_annotations.filter(validation_complete=False).count()
                n_confirmed = all_annotations.filter(validation_complete=True, revise=False).count()
                n_revised = all_annotations.filter(validation_complete=True, revise=True).count()


            n_spain = all_annotations.filter( Q(report__country__isnull=True) | Q(report__country__gid=17) ).count()
            n_europe = all_annotations.filter(Q(report__country__isnull=False) & ~Q(report__country__gid=17) ).count()

            args['n_flagged'] = n_flagged
            args['n_hidden'] = n_hidden
            args['n_public'] = n_public
            args['n_unchecked'] = n_unchecked
            args['n_confirmed'] = n_confirmed
            args['n_revised'] = n_revised
            args['n_loc_spain'] = n_spain
            args['n_loc_europe'] = n_europe
            args['n_loc_all'] = n_spain + n_europe

        if version_uuid and version_uuid != 'na':
            all_annotations = all_annotations.filter(report__version_UUID=version_uuid)
        if linked_id and linked_id != 'na':
            all_annotations = all_annotations.filter(linked_id=linked_id)
        if tags_filter and tags_filter != 'na' and tags_filter!='':
            tags_array = tags_filter.split(",")
            # we must go up to Report to filter tags, because you don't want to filter only your own tags but the tag that
            # any expert has put on the report
            # these are all (not only yours, but also) the reports that contain the filtered tag
            everyones_tagged_reports = ExpertReportAnnotation.objects.filter(tags__name__in=tags_array).values('report').distinct()
            # we want the annotations of the reports which contain the tag(s)
            all_annotations = all_annotations.filter(report__in=everyones_tagged_reports)
        if (not version_uuid or version_uuid == 'na') and (not linked_id or linked_id == 'na') and (not tags_filter or tags_filter == 'na' or tags_filter==''):
            if year and year != 'all':
                try:
                    this_year = int(year)
                    all_annotations = all_annotations.filter(report__creation_time__year=this_year)
                except ValueError:
                    pass
            if tiger_certainty and tiger_certainty != 'all':
                try:
                    this_certainty = int(tiger_certainty)
                    #all_annotations = all_annotations.filter(tiger_certainty_category=this_certainty)
                    all_annotations = all_annotations.filter(category__id=this_certainty)
                except ValueError:
                    pass
            if site_certainty and site_certainty != 'all':
                try:
                    this_certainty = int(site_certainty)
                    all_annotations = all_annotations.filter(site_certainty_category=this_certainty)
                except ValueError:
                    pass

            if pending == "complete":
                all_annotations = all_annotations.filter(validation_complete=True)
            elif pending == 'pending':
                all_annotations = all_annotations.filter(validation_complete=False)
            if status == "flagged":
                all_annotations = all_annotations.filter(status=0)
            elif status == "hidden":
                all_annotations = all_annotations.filter(status=-1)
            elif status == "public":
                all_annotations = all_annotations.filter(status=1)

            if this_user_is_superexpert:
                if checked == "unchecked":
                    all_annotations = all_annotations.filter(validation_complete=False)
                elif checked == "confirmed":
                    all_annotations = all_annotations.filter(validation_complete=True, revise=False)
                elif checked == "revised":
                    all_annotations = all_annotations.filter(validation_complete=True, revise=True)

                if final_status == "flagged":
                    all_annotations = all_annotations.filter(report__in=flagged_final_reports)
                elif final_status == "hidden":
                    all_annotations = all_annotations.filter(report__in=hidden_final_reports)
                elif final_status == "public":
                    all_annotations = all_annotations.filter(report__in=public_final_reports).exclude(report__in=flagged_final_reports).exclude(report__in=hidden_final_reports)

                if loc == 'spain':
                    all_annotations = all_annotations.filter( Q(report__country__isnull=True) | Q(report__country__gid=17) )
                elif loc == 'europe':
                    all_annotations = all_annotations.filter( Q(report__country__isnull=False) & ~Q(report__country__gid=17) )
                else:
                    pass

        if all_annotations:
            all_annotations = all_annotations.order_by('-report__creation_time')
            if orderby == "tiger_score":
                all_annotations = all_annotations.order_by('category__name')
            # if orderby == "site_score":
            #     all_annotations = all_annotations.order_by('site_certainty_category')
            # elif orderby == "tiger_score":
            #     all_annotations = all_annotations.order_by('tiger_certainty_category')
        paginator = Paginator(all_annotations, int(tasks_per_page))
        page = request.GET.get('page', 1)
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
        #current_pending = ExpertReportAnnotation.objects.filter(user=this_user).filter(validation_complete=False).count()
        current_pending = ExpertReportAnnotation.objects.filter(user=this_user).filter(validation_complete=False).filter(report__type='adult').count()
        args['n_pending'] = current_pending
        #n_complete = ExpertReportAnnotation.objects.filter(user=this_user).filter(validation_complete=True).count()
        n_complete = ExpertReportAnnotation.objects.filter(user=this_user).filter(validation_complete=True).filter(report__type='adult').count()
        args['n_complete'] = n_complete
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
        args['loc'] = loc
        args['status'] = status
        args['final_status'] = final_status
        args['version_uuid'] = version_uuid
        args['linked_id'] = linked_id
        args['tags_filter'] = tags_filter
        #args['my_version_uuids'] = my_version_uuids
        args['my_linked_ids'] = my_linked_ids
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
        args['other_species_culicidae'] = OtherSpecies.objects.filter(category='Culicidae').order_by('name')

        expert_users = User.objects.filter(groups__name='expert').order_by('first_name', 'last_name')
        expert_users_w_country = UserStat.objects.filter(user_id__in=expert_users).filter(native_of_id__isnull=False).exclude(native_of_id=17).values('native_of_id').distinct()
        args['country_name'] = EuropeCountry.objects.filter(gid__in=expert_users_w_country).order_by('name_engl').values('name_engl','iso3_code')

        return render(request, 'tigacrafting/expert_report_annotation.html' if this_user_is_expert else 'tigacrafting/superexpert_report_annotation.html', args)
    else:
        return HttpResponse("You need to be logged in as an expert member to view this page. If you have have been recruited as an expert and have lost your log-in credentials, please contact MoveLab.")

@login_required
def single_report_view(request,version_uuid=None):
    this_user = request.user
    version_uuid = request.GET.get('version_uuid', version_uuid)
    reports = Report.objects.filter(version_UUID=version_uuid)
    report = reports.first()
    who_has_list = []
    if report:
        these_annotations = ExpertReportAnnotation.objects.filter(report=report)
        for ano in these_annotations:
            if ano.user.username != this_user.username and not ano.user.userstat.is_superexpert():
                who_has_list.append( '<span class="label ' + ('label-success' if ano.validation_complete else 'label-warning') + '" data-toggle="tooltip" data-placement="bottom" title="' + (('validated by expert') if ano.validation_complete else ('pending with expert')) + '">expert <span class="glyphicon ' + ('glyphicon-check' if ano.validation_complete else 'glyphicon-time') + '"></span></span>' )
            else:
                who_has_list.append('<span class="label ' + ('label-success' if ano.validation_complete else 'label-warning') + '" data-toggle="tooltip" data-placement="bottom" title="' + (('validated by ' + ano.user.username) if ano.validation_complete else ('pending with ' + ano.user.username)) + '">' + ano.user.username + '<span class="glyphicon ' + ('glyphicon-check' if ano.validation_complete else 'glyphicon-time') + '"></span></span>')
    context = {'reports': reports, 'version_uuid' : version_uuid, 'this_user': this_user.username, 'who_has_list': who_has_list}
    return render(request, 'tigacrafting/single_report_view.html', context)


@login_required
def expert_report_status(request, reports_per_page=10, version_uuid=None, linked_id=None):
    this_user = request.user
    if this_user.groups.filter(Q(name='superexpert') | Q(name='movelab')).exists():
        version_uuid = request.GET.get('version_uuid', version_uuid)
        reports_per_page = request.GET.get('reports_per_page', reports_per_page)
        #all_reports_version_uuids = Report.objects.filter(type__in=['adult', 'site']).values('version_UUID')
        #all_reports_version_uuids = Report.objects.filter(type='adult').values('version_UUID')
        #these_reports = Report.objects.exclude(creation_time__year=2014).exclude(hide=True).exclude(photos__isnull=True).filter(type__in=['adult', 'site'])
        these_reports = Report.objects.exclude(creation_time__year=2014).exclude(hide=True).exclude(photos__isnull=True).filter(type='adult').order_by('-creation_time')
        if version_uuid and version_uuid != 'na':
            reports = Report.objects.filter(version_UUID=version_uuid)
            n_reports = 1
        elif linked_id and linked_id != 'na':
            reports = Report.objects.filter(linked_id=linked_id)
            n_reports = 1
        else:
            #reports = list(filter_reports(these_reports, sort=False))
            reports = list(fast_filter_reports(these_reports))
            n_reports = len(reports)
        paginator = Paginator(reports, int(reports_per_page))
        page = request.GET.get('page', 1)
        try:
            objects = paginator.page(page)
        except PageNotAnInteger:
            objects = paginator.page(1)
        except EmptyPage:
            objects = paginator.page(paginator.num_pages)
        paged_reports = Report.objects.filter(version_UUID__in=[object.version_UUID for object in objects]).order_by('-creation_time')
        reports_per_page_choices = range(0, min(1000, n_reports)+1, 25)
        #context = {'reports': paged_reports, 'all_reports_version_uuids': all_reports_version_uuids, 'version_uuid': version_uuid, 'reports_per_page_choices': reports_per_page_choices}
        context = {'reports': paged_reports, 'version_uuid': version_uuid, 'reports_per_page_choices': reports_per_page_choices}
        context['objects'] = objects
        context['pages'] = range(1, objects.paginator.num_pages+1)

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
    for var in x:
        reports.append(reportannotation_formatter(var))

    context = {'pendingReports': reports}

    return Response(context)


@api_view(['GET'])
def expert_report_complete(request):
    user = request.query_params.get('u', None)
    u = User.objects.get(username=user)
    x = ExpertReportAnnotation.objects.filter(user=u, validation_complete=True)

    reports = []
    for var in x:
        reports.append(reportannotation_formatter(var))

    context = {'completeReports': reports}

    return Response(context)

def get_reports_unfiltered_sites_embornal(reports_imbornal):
    new_reports_unfiltered_sites_embornal = Report.objects.exclude(type='adult').filter(
        version_UUID__in=reports_imbornal).exclude(note__icontains='#345').exclude(photos=None).annotate(
        n_annotations=Count('expert_report_annotations')).filter(n_annotations=0).order_by('-creation_time').all()
    return new_reports_unfiltered_sites_embornal

def get_reports_unfiltered_sites_other(reports_imbornal):
    new_reports_unfiltered_sites_other = Report.objects.exclude(type='adult').exclude(
        version_UUID__in=reports_imbornal).exclude(note__icontains='#345').exclude(photos=None).annotate(
        n_annotations=Count('expert_report_annotations')).filter(n_annotations=0).order_by('-creation_time').all()
    return new_reports_unfiltered_sites_other

def get_reports_imbornal():
    reports_imbornal = ReportResponse.objects.filter(
        Q(question='Is this a storm drain or sewer?', answer='Yes') | Q(question=u'\xc9s un embornal o claveguera?',
                                                                        answer=u'S\xed') | Q(
            question=u'\xbfEs un imbornal o alcantarilla?', answer=u'S\xed') | Q(question='Selecciona lloc de cria',
                                                                                 answer='Embornals') | Q(
            question='Selecciona lloc de cria', answer='Embornal o similar') | Q(question='Tipo de lugar de cría',
                                                                                 answer='Sumidero o imbornal') | Q(
            question='Tipo de lugar de cría', answer='Sumideros') | Q(question='Type of breeding site',
                                                                      answer='Storm drain') | Q(
            question='Type of breeding site', answer='Storm drain or similar receptacle')).values('report').distinct()

    reports_imbornal_new = ReportResponse.objects.filter(question_id=12).filter(answer_id=121).values('report').distinct()

    return  reports_imbornal | reports_imbornal_new

def get_reports_unfiltered_adults_except_being_validated():
    new_reports_unfiltered_adults = Report.objects.exclude(creation_time__year=2014).exclude(type='site').exclude(note__icontains='#345').exclude(photos=None).annotate(n_annotations=Count('expert_report_annotations')).filter(n_annotations=0).order_by('-server_upload_time')
    return new_reports_unfiltered_adults

def get_reports_unfiltered_adults():
    new_reports_unfiltered_adults = Report.objects.exclude(creation_time__year=2014).exclude(type='site').exclude(note__icontains='#345').exclude(photos=None).annotate(n_annotations=Count('expert_report_annotations')).filter(n_annotations__lt=3).order_by('-server_upload_time')
    return new_reports_unfiltered_adults

@login_required
def picture_validation(request,tasks_per_page='10',visibility='visible', usr_note='', type='all'):
    this_user = request.user
    this_user_is_superexpert = this_user.groups.filter(name='superexpert').exists()
    if this_user_is_superexpert:
        args = {}
        args.update(csrf(request))
        PictureValidationFormSet = modelformset_factory(Report, form=PhotoGrid, extra=0, can_order=True)
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
                                photo = report.photos.first()
                                new_annotation = ExpertReportAnnotation(report=report, user=this_user)
                                new_annotation.site_certainty_notes = 'auto'
                                new_annotation.best_photo_id = photo.id
                                new_annotation.validation_complete = True
                                new_annotation.revise = True
                                new_annotation.save()

###############------------------------------ FI FastUpload --------------------------------###############

            page = request.POST.get('page')
            visibility = request.POST.get('visibility')
            usr_note = request.POST.get('usr_note')
            type = request.POST.get('type', type)

            if not page:
                page = '1'
            return HttpResponseRedirect(reverse('picture_validation') + '?page=' + page + '&tasks_per_page='+tasks_per_page + '&visibility=' + visibility + '&usr_note=' + urllib.parse.quote_plus(usr_note) + '&type=' + type)
        else:
            tasks_per_page = request.GET.get('tasks_per_page', tasks_per_page)
            type = request.GET.get('type', type)
            visibility = request.GET.get('visibility', visibility)
            usr_note = request.GET.get('usr_note', usr_note)

        #new_reports_unfiltered_adults = get_reports_unfiltered_adults()
        new_reports_unfiltered_adults = get_reports_unfiltered_adults_except_being_validated()

        reports_imbornal = get_reports_imbornal()
        new_reports_unfiltered_sites_embornal = get_reports_unfiltered_sites_embornal(reports_imbornal)
        new_reports_unfiltered_sites_other = get_reports_unfiltered_sites_other(reports_imbornal)
        new_reports_unfiltered_sites = new_reports_unfiltered_sites_embornal | new_reports_unfiltered_sites_other

        new_reports_unfiltered = new_reports_unfiltered_adults | new_reports_unfiltered_sites

        #new_reports_unfiltered = Report.objects.exclude(creation_time__year=2014).exclude(note__icontains='#345').exclude(photos=None).annotate(n_annotations=Count('expert_report_annotations')).filter(n_annotations=0).order_by('-server_upload_time')
        if type == 'adult':
            #new_reports_unfiltered = new_reports_unfiltered.exclude(type='site')
            new_reports_unfiltered = new_reports_unfiltered_adults
        elif type == 'site':
            #new_reports_unfiltered = new_reports_unfiltered.exclude(type='adult')
            new_reports_unfiltered = new_reports_unfiltered_sites_embornal
        elif type == 'site-o':
            new_reports_unfiltered = new_reports_unfiltered_sites_other
        if visibility == 'visible':
            new_reports_unfiltered = new_reports_unfiltered.exclude(hide=True)
        elif visibility == 'hidden':
            new_reports_unfiltered = new_reports_unfiltered.exclude(hide=False)
        if usr_note and usr_note != '':
            new_reports_unfiltered = new_reports_unfiltered.filter(note__icontains=usr_note)

        new_reports_unfiltered = filter_reports(new_reports_unfiltered,False)

        new_reports_unfiltered = list(new_reports_unfiltered)

        paginator = Paginator(new_reports_unfiltered, int(tasks_per_page))
        page = request.GET.get('page', 1)
        try:
            objects = paginator.page(page)
        except PageNotAnInteger:
            objects = paginator.page(1)
        except EmptyPage:
            objects = paginator.page(paginator.num_pages)
        page_query = Report.objects.filter(version_UUID__in=[object.version_UUID for object in objects]).order_by('-creation_time')
        this_formset = PictureValidationFormSet(queryset=page_query)
        args['formset'] = this_formset
        args['objects'] = objects
        args['pages'] = range(1, objects.paginator.num_pages + 1)
        args['new_reports_unfiltered'] = page_query
        args['tasks_per_page'] = tasks_per_page
        args['visibility'] = visibility
        args['usr_note'] = usr_note
        args['type'] = type
        type_readable = ''
        if type == 'site':
            type_readable = "Breeding sites - Storm drains"
        elif type == 'site-o':
            type_readable = "Breeding sites - Other"
        elif type == 'adult':
            type_readable = "Adults"
        elif type == 'all':
            type_readable = "All"
        args['type_readable'] = type_readable
        #n_query_records = new_reports_unfiltered.count()
        n_query_records = len(new_reports_unfiltered)
        args['n_query_records'] = n_query_records
        args['tasks_per_page_choices'] = range(5, min(100, n_query_records) + 1, 5)
        #return render(request, 'tigacrafting/photo_grid.html', {'new_reports_unfiltered' : page_query})
        return render(request, 'tigacrafting/photo_grid.html', args)
    else:
        return HttpResponse("You need to be logged in as an expert member to view this page. If you have have been recruited as an expert and have lost your log-in credentials, please contact MoveLab.")


@login_required
def notifications(request,user_uuid=None):
    this_user = request.user
    user_uuid = request.GET.get('user_uuid',None)
    total_users = TigaUser.objects.all().count()
    return render(request, 'tigacrafting/notifications.html',{'user_id':this_user.id,'total_users':total_users, 'user_uuid':user_uuid})


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