import json
from django.http import HttpResponse
from django.views.generic import View
from django.db.models import Q
from operator import __or__ as OR

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
from django.contrib.auth import authenticate, login, logout

from models import MapAuxReports
from resources import MapAuxReportsResource
from django.db import connection
from jsonutils import DateTimeJSONEncoder
from dbutils import dictfetchall

from decorators import cross_domain_ajax


@csrf_exempt
@never_cache
@cross_domain_ajax
def ajax_login(request):
    if request.method == 'POST':
        response = {'success': False, 'data': {}}
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
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
    logout(request)
    return HttpResponse(json.dumps({}), content_type='application/json')


@never_cache
@cross_domain_ajax
def ajax_is_logged(request):
    response = {'success': False, 'data': {}}
    success = request.user.is_authenticated()
    if success is True:
        request.session.set_expiry(86400)
        response['success'] = True
        roles = request.user.groups.values_list('name', flat=True)
        response['data']['roles'] = list(roles)
    return HttpResponse(json.dumps(response),
                        content_type='application/json')


class MapAuxReportsExportView(View):

    def get(self, request, *args, **kwargs):

        authenticated = request.user.is_authenticated()
        if authenticated is True:
            filename = 'map_aux_reports_export'

            bbox = self.request.GET.get('bbox')

            if bbox is None:
                return HttpResponse('400 Bad Request', status=400)

            bbox = bbox.split(',')

            if len(bbox) is not 4:
                return HttpResponse('400 Bad Request', status=400)

            southwest_lng = bbox[0]
            southwest_lat = bbox[1]
            northeast_lng = bbox[2]
            northeast_lat = bbox[3]

            qs = MapAuxReports.objects.filter(
                lon__gte=southwest_lng
            ).filter(
                lon__lte=northeast_lng
            ).filter(
                lat__gte=southwest_lat
            ).filter(
                lat__lte=northeast_lat
            )

            year = self.request.GET.get('year')

            if year is not None:
                qs = qs.filter(observation_date__year=str(year))

            months = self.request.GET.get('months')
            if months is not None:
                months = months.split(',')
                lst = []
                for i in months:
                    lst.append(Q(observation_date__month=str(i).zfill(2)))
                qs = qs.filter(reduce(OR, lst))

            dataset = MapAuxReportsResource().export(qs)
            export_type = kwargs['format']
            _dataset_methods = {
                'csv': dataset.csv,
                'xls': dataset.xls
            }
            response = HttpResponse(
                _dataset_methods[export_type], content_type=export_type
            )
            response[
                'Content-Disposition'
                ] = 'attachment; filename={filename}.{ext}'.format(
                    filename=filename,
                    ext=export_type
                )
            return response
        else:
            return HttpResponse('401 Unauthorized', status=401)


@cross_domain_ajax
def map_aux_reports_zoom_bounds(request, zoom, bounds):

    db = connection.cursor()

    res = {'num_rows': 0, 'rows': []}

    box = bounds.split(',')
    zoom = int(zoom)

    hashlength = 3

    if zoom < 4:
        hashlength = 2
    elif zoom >= 3 and zoom < 5:
        hashlength = 3
    elif zoom >= 5 and zoom < 9:
        hashlength = 4
    elif zoom >= 9 and zoom < 12:
        hashlength = 5
    elif zoom >= 12 and zoom < 15:
        hashlength = 7
    elif zoom >= 15:
        hashlength = 8

    sql = """
        select c, simplified_expert_validation_result, month,
        lon, lat, id from reports_map_data
        where geohashlevel={0} and
        simplified_expert_validation_result<>'site#other' and
        ST_Intersects(
            ST_Point(lon,lat), ST_MakeBox2D(ST_Point(%s,%s),ST_Point(%s,%s))
        )
        """.format(hashlength)

    db.execute(sql, box)
    rows = dictfetchall(db)

    res['rows'] = rows
    res['num_rows'] = db.rowcount

    return HttpResponse(json.dumps(res),
                        content_type='application/json')


@cross_domain_ajax
def map_aux_reports(request, id):

    db = connection.cursor()

    sql = """
    select *, TO_CHAR(observation_date, 'YYYYMM') AS month
    from map_aux_reports where id=%s
    """
    db.execute(sql, (id,))
    rows = dictfetchall(db)
    if db.rowcount == 1:
        return HttpResponse(json.dumps(rows[0], cls=DateTimeJSONEncoder),
                            content_type='application/json')

    return HttpResponse('404 Not found', status=404)


@cross_domain_ajax
def map_aux_reports_bounds(request, bounds):

    db = connection.cursor()

    res = {'num_rows': 0, 'rows': []}
    box = bounds.split(',')

    box = map(float, box)

    sql = """
        select *, TO_CHAR(observation_date, 'YYYYMM') AS month
        from map_aux_reports
        where
        simplified_expert_validation_result<>'site#other' and
        expert_validated IS true AND
        lon is not null and lat is not null
        AND
        ST_Intersects(
            ST_Point(lon,lat), ST_MakeBox2D(ST_Point(%s,%s),ST_Point(%s,%s))
        )
        """

    db.execute(sql, box)
    rows = dictfetchall(db)

    res['rows'] = rows
    res['num_rows'] = db.rowcount

    return HttpResponse(DateTimeJSONEncoder().encode(res),
                        content_type='application/json')
