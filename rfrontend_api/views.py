from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.views.decorators.cache import never_cache, cache_page
from django.contrib.auth import authenticate, login, logout
from rest_framework.decorators import api_view
from tigaserver_app.models import ExpertReportAnnotation
from rfrontend_api.serializers import ExpertReportAnnotationSerializer
import json

ACC_HEADERS = {'Access-Control-Allow-Origin': '*',
               'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
               'Access-Control-Max-Age': 1000,
               'Access-Control-Allow-Headers': '*'}


def cross_domain_ajax(func):
    """Set Access Control request headers."""
    def wrap(request, *args, **kwargs):
        # Firefox sends 'OPTIONS' request for cross-domain javascript call.
        if request.method != "OPTIONS":
            response = func(request, *args, **kwargs)
        else:
            response = HttpResponse()
        for k, v in ACC_HEADERS.items():
            response[k] = v
        return response
    return wrap

@csrf_exempt
@never_cache
@cross_domain_ajax
def user_is_logged(request):
    if request.method == 'GET':
        if request.user is not None and request.user.is_authenticated:
            return HttpResponse(json.dumps({'logged':True}), status=200)
    return HttpResponse(json.dumps({'logged':False}), status=401)

# Create your views here.
@csrf_exempt
@never_cache
@cross_domain_ajax
def ajax_login(request):
    """Ajax login."""
    if request.method == 'POST':
        response = {'success': False, 'data': {}}
        request_data = json.loads(request.body)
        username = request_data.get('username', '')
        password = request_data.get('password', '')
        user = authenticate(username=username, password=password)
        if user is not None and user.is_active:
            request.session.set_expiry(86400)
            login(request, user)
            request.session['user_id'] = user.id
            response['success'] = True
            roles = request.user.groups.values_list('name', flat=True)
            response['data']['roles'] = list(roles)

        return HttpResponse(json.dumps(response),
                            content_type='application/json')
    else:
        return HttpResponse('Unauthorized', status=401)


@csrf_exempt
@never_cache
@cross_domain_ajax
def ajax_logout(request):
    """Ajax logout."""
    if request.method == 'POST':
        logout(request)
        return HttpResponse(json.dumps({}), content_type='application/json')


@api_view(['GET'])
def user_reports(request):
    if request.method == 'GET':
        this_user = request.user
        done_reports = ExpertReportAnnotation.objects.filter(user=this_user).filter(validation_complete=True).order_by('-last_modified')
        pending_reports = ExpertReportAnnotation.objects.filter(user=this_user).filter(validation_complete=False).order_by('-last_modified')
        done_reports_serializer = ExpertReportAnnotationSerializer(done_reports, many=True)
        pending_reports_serializer = ExpertReportAnnotationSerializer(pending_reports, many=True)
        return HttpResponse(
            json.dumps({
                'done_reports': done_reports_serializer.data,
                'done_reports_count': done_reports.count(),
                'pending_reports': pending_reports_serializer.data,
                'pending_reports_count': pending_reports.count(),
            }),
            content_type='application/json'
        )