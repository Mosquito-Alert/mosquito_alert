from django.core.management.base import BaseCommand
import requests
import json
from tigacrafting.models import CrowdcraftingUser, CrowdcraftingResponse, CrowdcraftingTask
from tigacrafting.views import import_tasks
import dateutil.parser
import pytz
import datetime
from django.db.models import Max
from django.conf import settings
from zipfile import ZipFile
from io import BytesIO


class Command(BaseCommand):
    args = ''
    help = 'Updates data from tigacrafting project on crowdcrafting site'

    def handle(self, *args, **options):
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
        self.stdout.write('Successfully updated tigacrafting data' if len(errors) == 0 and len(warnings) == 0 else 'Errors:' + '\n'.join(errors) + 'Warnings:' + '\n'.join(warnings))