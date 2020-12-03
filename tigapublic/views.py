"""VIEWS.

List of endpoints identified at urls.py
"""
# -*- coding: utf-8 -*-
import json
from io import BytesIO
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from django.views.decorators.cache import never_cache, cache_page
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

# from decorators import cross_domain_ajax
from .forms import TinyMCEImageForm
from .libs.notifications import NotificationManager
from .libs.observations import ObservationManager
from .libs.stormdrains import (StormDrainData, StormDrainUploader,
                               StormDrainUserSetup)
from .libs.userfixes import UserfixesManager
from .libs.upload import ExcelUploader
from .libs.epidemiology import EpidemiologyData
from .libs.predictionmodels import predictionModels
from .models import MapAuxReports, Municipalities, Epidemiology
from .utils import CustomJSONEncoder
from tigapublic.constants import (compulsatory_epidemiology_fields,
                                  optional_epidemiology_fields,
                                  epi_templates_path, epi_form_file,
                                  vector_file_name,
                                  vector_file_ext,
                                  epidemiologist_editor_group,
                                  grid_vectors_models_folder,
                                  municipalities_vector_models_folder,
                                  municipalities_vector_file_name,
                                  municipalities_vector_file_ext,
                                  municipalities_virus_models_folder,
                                  municipalities_virus_file_name,
                                  municipalities_virus_file_ext,
                                  municipalities_geom_folder,
                                  municipalities_geom_file_name,
                                  municipalities_geom_file_ext,
                                  municipalities_sd_geom_folder,
                                  municipalities_sd_geom_file_name,
                                  municipalities_sd_geom_file_ext,
                                  vectors, virus, tiles_path,
                                  biting_rates_models_folder,
                                  biting_file_name, biting_file_ext
                                  )
# from tigapublic.constants import prediction_models_folder
import os
import gzip
from tablib import Dataset
from tigapublic.utils import get_directory_structure
import psycopg2
from django.conf import settings


def geojson(request, z, x, y):
    """Geojson for municipalities ."""
    db = settings.DATABASES['default']
    connection = psycopg2.connect(user=db['USER'],
                                  password=db['PASSWORD'],
                                  host=db['HOST'],
                                  port=db['PORT'],
                                  database=db['NAME'])
    cursor = connection.cursor()
    sql = ("SELECT row_to_json(fc) FROM ("
           "SELECT 'FeatureCollection' AS type, coalesce(array_to_json(array_agg(f)),'[]') AS features"
           " FROM (SELECT"
                "'Feature' AS type ,ST_AsGeoJSON(ST_SetSRID(ST_MakePoint(lon, lat), 4326),6)::json as geometry, id"
                ", (SELECT row_to_json(t) FROM ( SELECT "
                # "-- aqui van els camps que seran properites del geojson"
                        "id,type, note, codigoine"
                    ") AS t"
                ") AS properties "
        "FROM map_aux_reports, municipis_4326 mun where id is not null and mun.gid = map_aux_reports.municipality_id and "
            "St_Contains(tileBBox({}, {}, {}, 4326), ST_SetSRID(ST_MakePoint(lon, lat), 4326))"
    ") AS f) AS fc").format(z, x, y)

    cursor.execute(sql)
    dades = cursor.fetchall()[0]

    if not os.path.exists("{}/{}/{}/{}".format(tiles_path, z, x, y)):
        cachefile = "{}/{}/{}/{}".format(tiles_path, z, x, y)
        try:
            os.makedirs("{}/{}/{}".format(tiles_path, z, x))
        except OSError:
            pass

        with open(cachefile, "wb") as f:
            f.write(bytes(json.dumps(dades[0])))

    return HttpResponse(json.dumps(dades[0], cls=CustomJSONEncoder),
                        content_type='application/json')



# PYTHON 3
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
            'username': '', 'groups': []
        }
    }
    success = request.user.is_authenticated
    if success is True:
        request.session.set_expiry(86400)
        response['success'] = True
        response['data']['username'] = request.user.username
        for g in request.user.groups.all():
            response['data']['groups'].append(g.name)

    response['vector_models_by_grid'] = {}
    response['vector_models_by_municipality'] = {}
    response['virus_models_by_municipality'] = {}
    response['biting_models'] = {}

    path = (biting_rates_models_folder + '/')
    filename = biting_file_name + biting_file_ext
    response['biting_models'] = get_directory_structure(path, filename)

    isVectorDataAvailable = False
    filename = vector_file_name + vector_file_ext

    for v in vectors:
        path = (municipalities_vector_models_folder + v + '/')
        response['vector_models_by_municipality'][v] = get_directory_structure(path, filename)

        if (len(response['vector_models_by_municipality'][v]) > 0):
            isVectorDataAvailable = True

        path = (grid_vectors_models_folder + v + '/')
        response['vector_models_by_grid'][v] = get_directory_structure(path, filename)

    response['availableVectorData'] = isVectorDataAvailable

    isVirusDataAvailable = False
    filename = municipalities_virus_file_name + municipalities_virus_file_ext

    if success is True:
        for v in virus:
            path = (municipalities_virus_models_folder + v + '/')
            response['virus_models_by_municipality'][v] = get_directory_structure(path, filename)
            if (len(response['virus_models_by_municipality'][v]) > 0):
                isVirusDataAvailable = True

    response['availableVirusData'] = isVirusDataAvailable

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
                   dict(self.request.GET).items()}
        return ObservationManager(request, **filters).export(*args, **kwargs)


# @@ MAP @@ #
@cross_domain_ajax
# cache for one day
# @cache_page(36000)
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
def predictionModelData(request, vector, year, month):
    """Get Prediction Data. Date format %Y-%m-%d."""
    mode = 'grid'
    if len(month) == 1:
        month = month.rjust(2, '0')

    # Get file name based on date
    if (mode == 'grid'):
        filename = (grid_vectors_models_folder + str(vector) + '/' +
                    str(year) + '/' + str(month) + '/' +
                    vector_file_name + vector_file_ext)
    else:
        filename = (municipalities_vector_models_folder + str(year) + '/' +
                    str(month) + '/' +
                    municipalities_vector_file_name +
                    municipalities_vector_file_ext)

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
        # print myModel.data.headers
        response = {}
        if (mode == 'grid'):
            response['prob'] = myModel.getProbGeometries()
            response['sd'] = myModel.getSdGeometries()
        else:
            with open(filename, 'r') as file:
                response = file.read()

        myModel.response = response
        return myModel._end_gz()
    else:
        return HttpResponse(status=404)


##################
# COMUNITI GEOMS #
##################

# For now is unused. Geometries are static files
@cache_page(36000)
def regionGeometries(request, ccaa):
    """Get comunity Geometry."""
    filename = (municipalities_geom_folder + '/' +
                municipalities_geom_file_name + str(ccaa) +
                municipalities_geom_file_ext)

    # If file exist then get data and create JSON
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as file:
                data = file.read().replace('\n', '')
                # data = json.loads(file.read())
        except IOError:
            return HttpResponse(status=401)

        zbuf = BytesIO()
        zfile = gzip.GzipFile(mode='wb',
                              compresslevel=6,
                              fileobj=zbuf)
        # content = json.dumps(data, cls=CustomJSONEncoder)
        zfile.write(data.encode('utf-8'))
        zfile.close()

        compressed_content = zbuf.getvalue()
        response = HttpResponse(compressed_content)
        response['Content-Type'] = 'application/json'
        response['Content-Encoding'] = 'gzip'
        response['Content-Length'] = str(len(compressed_content))
        return response


# For now is unused. Geometries are static files
@cache_page(36000)
def regionSdGeometries(request, ccaa):
    """Get comunity Geometry."""
    filename = (municipalities_sd_geom_folder + '/' +
                municipalities_sd_geom_file_name + str(ccaa) +
                municipalities_sd_geom_file_ext)

    # If file exist then get data and create JSON
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as file:
                data = file.read().replace('\n', '')
                # data = json.loads(file.read())
        except IOError:
            return HttpResponse(status=401)

        zbuf = BytesIO()
        zfile = gzip.GzipFile(mode='wb',
                              compresslevel=6,
                              fileobj=zbuf)
        # content = json.dumps(data, cls=CustomJSONEncoder)
        zfile.write(data.encode('utf-8'))
        zfile.close()

        compressed_content = zbuf.getvalue()
        response = HttpResponse(compressed_content)
        response['Content-Type'] = 'application/json'
        response['Content-Encoding'] = 'gzip'
        response['Content-Length'] = str(len(compressed_content))
        return response


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


def getSpainRegionFromCoords(request, lon, lat):
    """Get the CCAA id from a coordinate."""
    qs = Municipalities.objects.all()
    cadena = ("St_Distance(ST_SetSRID(ST_Point(%s, %s), 4326),geom)" %
              (lon, lat))
    qs = qs.extra(select={'dist': cadena})
    qs = qs.order_by('dist')[:1]
    qs = qs[:1]

    results = []
    for r in qs:
        # Javascript autoco  mplete requires id, text
        results.append({
            'id': str(r.gid),
            'cod_ccaa': r.cod_ccaa
        })
    return HttpResponse(json.dumps(results, cls=CustomJSONEncoder),
                        content_type='application/json')
