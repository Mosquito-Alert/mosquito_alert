from django.shortcuts import render
import requests
import json
from tigacrafting.models import *
from tigaserver_app.models import Photo, Report
import dateutil.parser
from django.db.models import Count
import pytz
import datetime
from django.db.models import Max
from django.views.decorators.clickjacking import xframe_options_exempt
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from random import shuffle
from django.core.context_processors import csrf
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.conf import settings
from django.http import HttpResponse
from django.forms.models import modelformset_factory
from tigacrafting.forms import AnnotationForm, MovelabAnnotationForm, ExpertReportAnnotationForm, SuperExpertReportAnnotationForm
from zipfile import ZipFile
from io import BytesIO
from operator import attrgetter
from django.db.models import Q


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
        print '\n'.join(errors)
        print '\n'.join(warnings)
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
                print 'existing task'
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


def filter_reports(reports, sort=True):
    if sort:
        reports_filtered = sorted(filter(lambda x: not x.deleted and x.latest_version, reports), key=attrgetter('n_annotations'), reverse=True)
    else:
        reports_filtered = filter(lambda x: not x.deleted and x.latest_version, reports)
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


@login_required
def expert_report_annotation(request, scroll_position='', tasks_per_page='10', load_new_reports='F', year='all', orderby='date', tiger_certainty='all', site_certainty='all', pending='na', checked='na', status='all', final_status='na', max_pending=5, max_given=3, version_uuid='na', linked_id='na'):
    this_user = request.user
    this_user_is_expert = this_user.groups.filter(name='expert').exists()
    this_user_is_superexpert = this_user.groups.filter(name='superexpert').exists()
    this_user_is_team_bcn = this_user.groups.filter(name='team_bcn').exists()
    this_user_is_team_not_bcn = this_user.groups.filter(name='team_not_bcn').exists()

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
            status = request.POST.get('stats', status)
            final_status = request.POST.get('final_status', final_status)
            version_uuid = request.POST.get('version_uuid', version_uuid)
            linked_id = request.POST.get('linked_id', linked_id)
            checked = request.POST.get('checked', checked)
            formset = AnnotationFormset(request.POST)
            if formset.is_valid():
                formset.save()
                page = request.GET.get('page')
                if not page:
                    page = '1'
                return HttpResponseRedirect(reverse('expert_report_annotation') + '?page='+page+'&tasks_per_page='+tasks_per_page+'&scroll_position='+scroll_position+(('&pending='+pending) if pending else '') + (('&checked='+checked) if checked else '') + (('&final_status='+final_status) if final_status else '') + (('&='+version_uuid) if version_uuid else '') + (('&linked_id='+linked_id) if linked_id else '') + (('&orderby='+orderby) if orderby else '') + (('&tiger_certainty='+tiger_certainty) if tiger_certainty else '') + (('&site_certainty='+site_certainty) if site_certainty else '') + (('&status='+status) if status else ''))
            else:
                return HttpResponse('error')
        else:
            tasks_per_page = request.GET.get('tasks_per_page', tasks_per_page)
            scroll_position = request.GET.get('scroll_position', scroll_position)
            orderby = request.GET.get('orderby', orderby)
            tiger_certainty = request.GET.get('tiger_certainty', tiger_certainty)
            site_certainty = request.GET.get('site_certainty', site_certainty)
            pending = request.GET.get('pending', pending)
            status = request.GET.get('status', status)
            final_status = request.GET.get('final_status', final_status)
            version_uuid = request.GET.get('version_uuid', version_uuid)
            linked_id = request.GET.get('linked_id', linked_id)
            checked = request.GET.get('checked', checked)
            load_new_reports = request.GET.get('load_new_reports', load_new_reports)
            current_pending = ExpertReportAnnotation.objects.filter(user=this_user).filter(validation_complete=False).count()
            my_reports = ExpertReportAnnotation.objects.filter(user=this_user).values('report')
            flagged_others_reports = ExpertReportAnnotation.objects.exclude(user=this_user).filter(user__groups__name='expert').filter(validation_complete=True, status=0).values('report')
            hidden_others_reports = ExpertReportAnnotation.objects.exclude(user=this_user).filter(user__groups__name='expert').filter(validation_complete=True, status=-1).values('report')
            public_others_reports = ExpertReportAnnotation.objects.exclude(user=this_user).filter(user__groups__name='expert').filter(validation_complete=True, status=1).values('report')
            if this_user_is_expert and load_new_reports == 'T':
                if current_pending < max_pending:
                    n_to_get = max_pending - current_pending
                    new_reports_unfiltered = Report.objects.exclude(creation_time__year=2014).exclude(version_UUID__in=my_reports).exclude(hide=True).exclude(photos=None).annotate(n_annotations=Count('expert_report_annotations')).filter(n_annotations__lte=max_given)
                    if new_reports_unfiltered and this_user_is_team_bcn:
                        new_reports_unfiltered = new_reports_unfiltered.filter(Q(location_choice='selected', selected_location_lon__range=(BCN_BB['min_lon'],BCN_BB['max_lon']),selected_location_lat__range=(BCN_BB['min_lat'], BCN_BB['max_lat'])) | Q(location_choice='current', current_location_lon__range=(BCN_BB['min_lon'],BCN_BB['max_lon']), current_location_lat__range=(BCN_BB['min_lat'], BCN_BB['max_lat'])))
                    if new_reports_unfiltered and this_user_is_team_not_bcn:
                        new_reports_unfiltered = new_reports_unfiltered.exclude(Q(location_choice='selected', selected_location_lon__range=(BCN_BB['min_lon'],BCN_BB['max_lon']),selected_location_lat__range=(BCN_BB['min_lat'], BCN_BB['max_lat'])) | Q(location_choice='current', current_location_lon__range=(BCN_BB['min_lon'],BCN_BB['max_lon']),current_location_lat__range=(BCN_BB['min_lat'], BCN_BB['max_lat'])))
                    if new_reports_unfiltered:
                        new_reports = filter_reports(new_reports_unfiltered.order_by('creation_time'))
                        reports_to_take = new_reports[0:n_to_get]
                        for this_report in reports_to_take:
                            new_annotation = ExpertReportAnnotation(report=this_report, user=this_user)
                            new_annotation.save()
            elif this_user_is_superexpert:
                new_reports_unfiltered = Report.objects.exclude(creation_time__year=2014).exclude(version_UUID__in=my_reports).exclude(hide=True).exclude(photos=None).annotate(n_annotations=Count('expert_report_annotations')).filter(n_annotations__gte=max_given)
                if new_reports_unfiltered and this_user_is_team_bcn:
                        new_reports_unfiltered = new_reports_unfiltered.filter(Q(location_choice='selected', selected_location_lon__range=(BCN_BB['min_lon'],BCN_BB['max_lon']),selected_location_lat__range=(BCN_BB['min_lat'], BCN_BB['max_lat'])) | Q(location_choice='current', current_location_lon__range=(BCN_BB['min_lon'],BCN_BB['max_lon']),current_location_lat__range=(BCN_BB['min_lat'], BCN_BB['max_lat'])))
                if new_reports_unfiltered and this_user_is_team_not_bcn:
                        new_reports_unfiltered = new_reports_unfiltered.exclude(Q(location_choice='selected', selected_location_lon__range=(BCN_BB['min_lon'],BCN_BB['max_lon']),selected_location_lat__range=(BCN_BB['min_lat'], BCN_BB['max_lat'])) | Q(location_choice='current', current_location_lon__range=(BCN_BB['min_lon'],BCN_BB['max_lon']),current_location_lat__range=(BCN_BB['min_lat'], BCN_BB['max_lat'])))
                if new_reports_unfiltered:
                    new_reports = filter_reports(new_reports_unfiltered, sort=False)
                    for this_report in new_reports:
                        new_annotation = ExpertReportAnnotation(report=this_report, user=this_user)
                        new_annotation.save()
            all_annotations = ExpertReportAnnotation.objects.filter(user=this_user)
            my_version_uuids = all_annotations.values('report__version_UUID')
            my_linked_ids = all_annotations.values('linked_id')
            if this_user_is_expert:
                if not pending or pending == 'na':
                    pending = 'pending'
            if this_user_is_superexpert:
                if not final_status or final_status == 'na':
                    final_status = 'public'
                if not checked or checked == 'na':
                    checked = 'unchecked'
                n_flagged = all_annotations.filter(report__in=flagged_others_reports).count()
                n_hidden = all_annotations.filter(report__in=hidden_others_reports).count()
                n_public = all_annotations.filter(report__in=public_others_reports).exclude(report__in=flagged_others_reports).exclude(report__in=hidden_others_reports).count()
                n_unchecked = all_annotations.filter(validation_complete=False).count()
                n_confirmed = all_annotations.filter(validation_complete=True, revise=False).count()
                n_revised = all_annotations.filter(validation_complete=True, revise=True).count()
                args['n_flagged'] = n_flagged
                args['n_hidden'] = n_hidden
                args['n_public'] = n_public
                args['n_unchecked'] = n_unchecked
                args['n_confirmed'] = n_confirmed
                args['n_revised'] = n_revised
            if version_uuid and version_uuid != 'na':
                all_annotations = all_annotations.filter(report__version_UUID=version_uuid)
            if linked_id and linked_id != 'na':
                all_annotations = all_annotations.filter(linked_id=linked_id)
            if (not version_uuid or version_uuid == 'na') and (not linked_id or linked_id == 'na'):
                if year and year != 'all':
                    try:
                        this_year = int(year)
                        all_annotations = all_annotations.filter(report__creation_time__year=this_year)
                    except ValueError:
                        pass
                if tiger_certainty and tiger_certainty != 'all':
                    try:
                        this_certainty = int(tiger_certainty)
                        all_annotations = all_annotations.filter(tiger_certainty_category=this_certainty)
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
                        all_annotations = all_annotations.filter(report__in=flagged_others_reports)
                    elif final_status == "hidden":
                        all_annotations = all_annotations.filter(report__in=hidden_others_reports)
                    elif final_status == "public":
                        all_annotations = all_annotations.filter(report__in=public_others_reports).exclude(report__in=flagged_others_reports).exclude(report__in=hidden_others_reports)
            if all_annotations:
                all_annotations = all_annotations.order_by('report__creation_time')
                if orderby == "site_score":
                    all_annotations = all_annotations.order_by('site_certainty_category')
                elif orderby == "tiger_score":
                    all_annotations = all_annotations.order_by('tiger_certainty_category')
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
            current_pending = ExpertReportAnnotation.objects.filter(user=this_user).filter(validation_complete=False).count()
            args['n_pending'] = current_pending
            n_complete = ExpertReportAnnotation.objects.filter(user=this_user).filter(validation_complete=True).count()
            args['n_complete'] = n_complete
            args['n_total'] = n_complete + current_pending
            args['year'] = year
            args['orderby'] = orderby
            args['tiger_certainty'] = tiger_certainty
            args['site_certainty'] = site_certainty
            args['pending'] = pending
            args['checked'] = checked
            args['status'] = status
            args['final_status'] = final_status
            args['version_uuid'] = version_uuid
            args['linked_id'] = linked_id
            args['my_version_uuids'] = my_version_uuids
            args['my_linked_ids'] = my_linked_ids
            args['tasks_per_page'] = tasks_per_page
            args['scroll_position'] = scroll_position
            args['tasks_per_page_choices'] = range(5, min(100, all_annotations.count())+1, 5)
        return render(request, 'tigacrafting/expert_report_annotation.html' if this_user_is_expert else 'tigacrafting/superexpert_report_annotation.html', args)
    else:
        return HttpResponse("You need to be logged in as an expert member to view this page. If you have have been recruited as an expert and have lost your log-in credentials, please contact MoveLab.")