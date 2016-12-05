import json
from django.http import HttpResponse
from StringIO import StringIO
from zipfile import ZipFile
from django.views.generic import View
from django.db import models
from django.db.models import Q, CharField
from operator import __or__ as OR

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
from django.contrib.auth import authenticate, login, logout

from models import MapAuxReports
from resources import MapAuxReportsResource
from django.db import connection
from jsonutils import DateTimeJSONEncoder
from dbutils import dictfetchall

from constants import *
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

#from django.db import connection
class MapAuxReportsExportView(View):

    def time_filter(self, qs):
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

        return qs

    def bbox_filter(self, qs):
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

        qs = qs.filter(
            lon__gte=southwest_lng
        ).filter(
            lon__lte=northeast_lng
        ).filter(
            lat__gte=southwest_lat
        ).filter(
            lat__lte=northeast_lat
        )
        return qs

    def category_filter(self, qs):
        categories = self.request.GET.get('categories')
        args = Q()
        if categories is not None:
            categories = categories.split(',')
            for c in categories:
                args.add(Q(private_webmap_layer=c), Q.OR)

        qs = qs.filter(args)
        return qs

    def get(self, request, *args, **kwargs):

        authenticated = request.user.is_authenticated()
        if authenticated is True:
            filename = 'mosquito_alert'

            qs = MapAuxReports.objects.all()

            qs = self.bbox_filter(qs)
            qs = self.time_filter(qs)
            qs = self.category_filter(qs)
            qs = qs.order_by('-observation_date')

            dataset = MapAuxReportsResource().export(qs)
            export_type = kwargs['format']
            _dataset_methods = {
                'csv': dataset.csv,
                'xls': dataset.xls
            }

            response = HttpResponse(
                _dataset_methods[export_type], content_type=export_type
            )
            
            license_file = open("/home/sites/sigserver3.udg.edu/wsgi_apps/mosquito/app/tigapublic/files/license.txt")
            metadata_file = open("/home/sites/sigserver3.udg.edu/wsgi_apps/mosquito/app/tigapublic/files/metadata.xlsx")
            
            in_memory = StringIO()
            zip = ZipFile(in_memory, "a")
            zip.writestr("license.txt", license_file.read())
            zip.writestr("metadata.xlsx", metadata_file.read())
            zip.writestr("data.xls", _dataset_methods[export_type])
            
            # fix for Linux zip files read in Windows
            for file in zip.filelist:
                file.create_system = 0

            zip.close()

            response = HttpResponse(mimetype="application/zip")
            response["Content-Disposition"] = "attachment; filename=mosquito_alert.zip"

            in_memory.seek(0)
            response.write(in_memory.read())

            return response
        else:
            return HttpResponse('401 Unauthorized', status=401)


@cross_domain_ajax
def map_aux_reports_zoom_bounds(request, zoom, bounds):

    db = connection.cursor()

    res = {'num_rows': 0, 'rows': []}

    box = bounds.split(',')
    zoom = int(zoom)

    if zoom < 5:
        hashlength = 3
    elif zoom < 9:
        hashlength = 4
    elif zoom < 12:
        hashlength = 5
    elif zoom < 15:
        hashlength = 7
    else:
        hashlength = 8

    sql = """
        select c, category, expert_validation_result, month,
        lon, lat, id from reports_map_data
        where geohashlevel={0} and
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
        select c, category, expert_validation_result, month,
        lon, lat, id from reports_map_data
        where geohashlevel=8 and
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

def userfixes(request, year, months):

    db = connection.cursor()

    sql_head = """
        SELECT
            ST_AsGeoJSON(ST_Expand(ST_MakePoint(masked_lon + 0.025, masked_lat + 0.025),0.025)) AS geometry,
            count(*) AS n_fixes
        FROM tigaserver_app_fix
    """

    sql_foot = """
        GROUP BY masked_lon, masked_lat
        ORDER BY masked_lat, masked_lon
    """

    if year == 'all' and months == 'all':
        sql = sql_head + sql_foot
    elif year == 'all':
        sql = sql_head + """
            WHERE extract(month FROM fix_time) in ("""+months+""")
        """ + sql_foot
    elif months == 'all':
        sql = sql_head + """
            WHERE extract(year FROM fix_time) = """+year+"""
        """ + sql_foot
    else:
        sql = sql_head + """
            WHERE extract(year FROM fix_time) = """+year+"""
            AND extract(month FROM fix_time) in ("""+months+""")
        """ + sql_foot

    db.execute(sql)

    rows = []
    for row in db.fetchall():
        data = {
            'geometry': json.loads(row[0]),
            #'id': row[1],
            'type': 'Feature',
            'properties': {
                'num_fixes': row[1]
            }
        }
        rows.append(data)

    db.close()

    res = {'type': 'FeatureCollection', 'features': rows}

    return HttpResponse(DateTimeJSONEncoder().encode(res),
                        content_type='application/json')

def reports(request, bounds, year, months, categories):

    db = connection.cursor()

    res = {'num_rows': 0, 'rows': []}
    box = bounds.split(',')

    # Get and prepare categories param for the sql
    layers = categories.split(',')
    cat = "'" + "', '".join([i for i in layers]) + "'"

    box = map(float, box)

    sql = """
        select *, TO_CHAR(observation_date, 'YYYYMM') AS month,
           private_webmap_layer AS category
        from map_aux_reports
        where
        lon is not null and lat is not null
        AND
        ST_Intersects(
            ST_Point(lon,lat), ST_MakeBox2D(ST_Point(%s,%s),ST_Point(%s,%s))
        )
    """

    # And date and layers filters to sql
    filters = ""

    if year != 'all':
        filters = " and extract(year from observation_date) = "+year

    if months != 'all':
        filters += " and extract(month from observation_date) in (" + months + ")"


    sql += filters

    sql += " ORDER BY observation_date DESC "

    sql = "SELECT * FROM (" + sql +") as foo where category in (" + cat + ") LIMIT " + str(maxReports)

    db.execute(sql, box)
    rows = dictfetchall(db)

    res['sql'] = sql
    res['categories'] = categories
    res['rows'] = rows
    res['num_rows'] = len(rows)

    return HttpResponse(DateTimeJSONEncoder().encode(res),
                        content_type='application/json')
