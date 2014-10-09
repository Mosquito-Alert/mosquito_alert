from django.shortcuts import render
import requests
import json
from tigacrafting.models import *
from tigaserver_app.models import Photo
import dateutil.parser


def import_tasks():
    r = requests.get('http://crowdcrafting.org/app/Tigafotos/tasks/export?type=task&format=json')
    task_array = json.loads(r.text)
    errors = []
    warnings = []
    for task in task_array:
        existing_task = CrowdcraftingTask.objects.filter(task_id=task['id'])
        if not existing_task:
            task_model = CrowdcraftingTask()
            task_model.task_id = task['id']
            existing_photo = Photo.objects.filter(id=int(task['info'][u'\ufeffid']))
            if existing_photo:
                this_photo = Photo.objects.get(id=task['info'][u'\ufeffid'])
                task_model.photo = this_photo
                task_model.save()
            else:
                errors.append('Photo with id=' + task['info'][u'\ufeffid'] + ' does not exist.')
        else:
            warnings.append('Task ' + str(existing_task[0].task_id) + ' already exists, not saved.')
    print '\n'.join(errors)
    print '\n'.join(warnings)
    return {'errors': errors, 'warnings': warnings}


def import_task_responses():
    r = requests.get('http://crowdcrafting.org/app/Tigafotos/tasks/export?type=task_run&format=json')
    response_array = json.loads(r.text)
    errors = []
    warnings = []
    for response in response_array:
        info_dic = {}
        info_fields = response['info'].replace('{', '').replace(' ', '').replace('}', '').split(',')
        for info_field in info_fields:
            info_dic[info_field.split(':')[0]] = info_field.split(':')[1]
        response_model = CrowdcraftingResponse()
        response_model.created = dateutil.parser.parse(response['created'])
        response_model.finish_time = dateutil.parser.parse(response['finish_time'])
        response_model.mosquito_question_response = info_dic['mosquito']
        response_model.tiger_question_response = info_dic['tiger']
        response_model.site_question_response = info_dic['site']
        response_model.user_ip = response['user_ip']
        response_model.user_lang = info_dic['user_lang']
        existing_task = CrowdcraftingTask.objects.filter(task_id=response['task_id'])
        if existing_task:
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
                break
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
    print '\n'.join(errors)
    print '\n'.join(warnings)
    return {'errors': errors, 'warnings': warnings}


