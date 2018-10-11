"""VIEWS.

List of endpoints identified at urls.py
"""
# -*- coding: utf-8 -*-
import json
import sys

from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from django.views.decorators.cache import never_cache, cache_page
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from decorators import cross_domain_ajax
from forms import TinyMCEImageForm
from libs.notifications import NotificationManager
from libs.observations import ObservationManager
from libs.stormdrains import (StormDrainData, StormDrainUploader,
                              StormDrainUserSetup)
from libs.userfixes import UserfixesManager
from libs.upload import ExcelUploader
from libs.epidemiology import EpidemiologyData
from libs.predictionmodels import predictionModels
from models import MapAuxReports, Municipalities, Epidemiology
from utils import CustomJSONEncoder
from tigapublic.constants import (compulsatory_epidemiology_fields,
                                  optional_epidemiology_fields,
                                  epi_templates_path, epi_form_file,
                                  prediction_file_name,
                                  prediction_file_ext,
                                  epidemiologist_editor_group,
                                  prediction_models_folder
                                  )
# from tigapublic.constants import prediction_models_folder
import os
from tablib import Dataset
from tigapublic.utils import get_directory_structure

reload(sys)
sys.setdefaultencoding('utf-8')


#########
# USERS #
#########
# TODO: Refactoring with classes?
@csrf_exempt
@never_cache
@cross_domain_ajax
def ajax_login(request):
    """Ajax login."""
    if request.method == 'POST':
        response = {'success': False, 'data': {}}
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
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


@never_cache
@cross_domain_ajax
def ajax_logout(request):
    """Ajax logout."""
    logout(request)
    return HttpResponse(json.dumps({}), content_type='application/json')


@never_cache
@cross_domain_ajax
def ajax_is_logged(request):
    """Ajax is logged."""
    response = {
        'success': False,
        'data': {
            'username': '', 'groups': [], 'roles': []
        }
    }
    success = request.user.is_authenticated()
    if success is True:
        request.session.set_expiry(86400)
        response['success'] = True
        response['data']['username'] = request.user.username
        for g in request.user.groups.all():
            response['data']['groups'].append(g.name)
        response['data']['roles'] = list(request.user.get_all_permissions())

    # Logged or not, check available models
    response['models'] = get_directory_structure(prediction_models_folder)

    return HttpResponse(json.dumps(response),
                        content_type='application/json')


#####################
# OBSERVATIONS DATA #
#####################
# @@ EXPORT @@ #
class ObservationsExportView(View):
    """Export xls files."""

    def get(self, request, *args, **kwargs):
        """Export data to Excel/CSV."""
        # Get filters from the request.GET
        filters = {key: value[0] for key, value in
                   dict(self.request.GET).iteritems()}
        return ObservationManager(request, **filters).export(*args, **kwargs)


# @@ MAP @@ #
@cross_domain_ajax
# cache for one day
@cache_page(36000)
def observations(request, **filters):
    """Get Data to Show on Map."""
    # Are there any filters (besides zoom and bounds)?
    filterscopy = filters.copy()
    if 'zoom' in filterscopy:
        del filterscopy['zoom']
    if 'bounds' in filterscopy:
        del filterscopy['bounds']

    model = False
    # If there are filters, use MapAuxReports
    if filterscopy:
        model = MapAuxReports

    return ObservationManager(request, **filters).get(model=model)


# @@ SINGLE @@ #
@cross_domain_ajax
def observation(request, id):
    """Get All data Of One Observation."""
    return ObservationManager(request).get_single(id)


# @@ REPORTS @@ #
def observations_report(request, **filters):
    """Get Reports."""
    return ObservationManager(request, **filters).get_report()


##############
# USER FIXES #
##############
def userfixes_get_gridsize(data):
    """Return the size of the grid."""
    # Focus on Barcelona (where we have maximum density of userfixes)
    griddata = data.filter(masked_lon__gt=1.9, masked_lat__gt=41.34)
    if griddata[0]['masked_lat'] == griddata[1]['masked_lat']:
        gridsize = griddata[1]['masked_lon'] - griddata[0]['masked_lon']
    else:
        gridsize = griddata[1]['masked_lat'] - griddata[0]['masked_lat']
    return gridsize


# def userfixes(request, years, months, date_start, date_end):
# cache for one day
@cache_page(36000)
def userfixes(request, **filters):
    """Get Coverage Layer Info."""
    manager = UserfixesManager(request)
    return manager.get('GeoJSON', **filters)


################
# STORM DRAINS #
################
@csrf_exempt
@never_cache
@cross_domain_ajax
def stormDrainSetup(request):
    """Manage the configuration of storm drain visualization.

    Only for registered users.

    GET:
    Get current stormdrain configuration.

    POST:
    Store the configuration for storm drains.
    """
    user_setup = StormDrainUserSetup(request)

    if request.method == 'GET':
        return user_setup.get()

    elif request.method == 'POST':
        return user_setup.put()


@csrf_exempt
@cross_domain_ajax
def stormDrainData(request):
    """Manage storm drain data.

    Only for registered users.

    GET:
    Get the storm drain data.

    POST:
    Upload a storm drain data file (XLS or CSV).

    """
    if request.method == 'GET':
        data_provider = StormDrainData(request)
        return data_provider.get()

    elif request.method == 'POST':
        uploader = StormDrainUploader(request)
        return uploader.put()


def getStormDrainTemplate(request):
    """Return the template used to import data."""
    uploader = StormDrainUploader(request)
    return uploader.get_template()

################
# EPIDEMIOLOGY #
################


@csrf_exempt
@cross_domain_ajax
def epidemiologyData(request):
    """Manage epidemiology data.

    Only for registered users.

    GET:
    Get epidemiology data.

    POST:
    Upload a epidemiology data file (XLS or CSV).

    """
    if request.method == 'GET':
        data_provider = EpidemiologyData(request)
        return data_provider.get()

    elif request.method == 'POST':

        if (epidemiologist_editor_group not in
                request.user.groups.values_list('name', flat=True)):
            return HttpResponse('Unauthorized', status=401)

        uploader = ExcelUploader(
                request=request,
                model=Epidemiology,
                compulsatory_fields=compulsatory_epidemiology_fields,
                optional_fields=optional_epidemiology_fields,
                template_location=epi_templates_path,
                template_zipped_name='epidemiology_template.zip',
                form_input_name=epi_form_file
                )
        return uploader.put()


def getEpidemiologyTemplate(request):
    """Return the template used to import data."""
    uploader = ExcelUploader(
                request=request,
                model=Epidemiology,
                compulsatory_fields=compulsatory_epidemiology_fields,
                optional_fields=optional_epidemiology_fields,
                template_location=epi_templates_path,
                template_zipped_name='epidemiology_template.zip',
                form_input_name=epi_form_file
                )
    return uploader.get_template()

#####################
# Prediction Models #
#####################


@cache_page(36000)
def predictionModelData(request, year, month):
    """Get Prediction Data. Date format %Y-%m-%d."""
    if len(month) == 1:
        month = month.rjust(2, '0')

    # Get file name based on date
    filename = (prediction_models_folder + str(year) + '/' +
                str(month) + '/' +
                prediction_file_name + prediction_file_ext)

    # If file exist then get data and create JSON
    if os.path.exists(filename):
        try:
            file = open(filename, 'r')
        except IOError:
            return HttpResponse(status=401)

        myModel = predictionModels(year, month)
        myModel.data = Dataset()
        myModel.data.load(file.read(), 'csv')
        # Lower case headers
        lowerHeaders = [h.lower() for h in myModel.data.headers]
        myModel.data.headers = lowerHeaders
        print myModel.data.headers
        response = {}
        response['prob'] = myModel.getProbGeometries()
        response['sd'] = myModel.getSdGeometries()
        myModel.response = response
        return myModel._end()
    else:
        return HttpResponse(status=404)


#################
# NOTIFICATIONS #
#################


@csrf_exempt
@never_cache
@cross_domain_ajax
def notifications(request):
    """Manage notifications."""
    if request.method == 'POST':
        # Save notifications to the database.
        return NotificationManager(request).save()


@csrf_exempt
@cross_domain_ajax
def imageupload(request):
    """Image Upload."""
    return TinyMCEImageForm(request.POST, request.FILES).save()


@csrf_exempt
@cross_domain_ajax
def notifications_intersecting(request, **filters):
    """Get Observations Inside Polygon Using DateRange param."""
    observations = ObservationManager(request, **filters)
    extra = {'select': {'user_id': "md5(user_id)"}}
    return observations.get_intersecting(extra)


@csrf_exempt
@never_cache
@cross_domain_ajax
def notifications_predefined(request, **kwargs):
    """Get a list of notification predefined templates.

    To be used to populate the notification form.
    """
    manager = NotificationManager(request)

    if 'only_my_own' not in kwargs:
        kwargs['only_my_own'] = False

    return manager.get_predefined_templates(kwargs['only_my_own'])


###########
# FILTERS #
###########
# TODO: Refactoring with classes
@csrf_exempt
@cross_domain_ajax
def getMunicipalities(request, search):
    """getMunicipalities."""
    search_qs = Municipalities.objects.filter(
            nombre__istartswith=request.GET['query']
        ).distinct().order_by('nombre')[:20]

    results = []
    for r in search_qs:
        # Javascript autoco  mplete requires id, text
        results.append({
            'id': str(r.gid),
            'label': r.nombre
        })
    return HttpResponse(json.dumps(results, cls=CustomJSONEncoder),
                        content_type='application/json')


@csrf_exempt
@cross_domain_ajax
def getMunicipalitiesById(request,):
    """getMunicipalitiesById."""
    if len(request.body.decode(encoding='UTF-8')) == 0:
        return HttpResponse({})

    municipalitiesArray = request.body.decode(encoding='UTF-8').split(',')
    int_array = map(int, municipalitiesArray)
    qs = Municipalities.objects.filter(
        gid__in=int_array
        ).distinct().order_by('nombre')

    results = {'data': []}
    for r in qs:
        # Javascript autoco  mplete requires id, text
        results['data'].append({
            'id': str(r.gid),
            'label': r.nombre
        })
    return HttpResponse(json.dumps(results, cls=CustomJSONEncoder),
                        content_type='application/json')
