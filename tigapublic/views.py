import json, decimal
from pyproj import Proj, transform
import tempfile
import django.db.models.fields
from django.db import transaction
import datetime
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

from django.contrib.gis.geos import GEOSGeometry, Polygon, LineString, Point
from models import MapAuxReports, Notification, NotificationContent, NotificationImageFormModel
from models import StormDrain, StormDrainUserVersions, AuthUser

from resources import MapAuxReportsLimitedResource, MapAuxReportsResource, MapAuxReportsExtendedResource
from resources import NotificationResource, NotificationExtendedResource, StormDrainResource, StormDrainCSVResource
from django.db import connection
from jsonutils import DateTimeJSONEncoder
from dbutils import dictfetchall

from constants import *
from django.conf import settings
from django import forms
from forms import *
import datetime
from tablib import Dataset
import os

from decorators import cross_domain_ajax

@csrf_exempt
@never_cache
@cross_domain_ajax
def save_notification(request):
    response = {'success': False}
    if request.method == 'POST':
        post = request.POST.copy()
        post['date_comment'] = datetime.datetime.now()
        # post['public'] = True
        post['user_id'] = '1'
        post['report_id'] = '1'
        post['public'] = True

        report_ids = request.POST.getlist('report_ids[]')

        success = request.user.is_authenticated()
        if success is True:
            if request.user is not None:
                if request.user.is_active and (request.user.groups.filter(name=managers_group).exists()
                    or request.user.groups.filter(name=superusers_group).exists() ):
                    response['user'] ='yes'
                    db = connection.cursor()
                    notif_content = NotificationContent(
                        body_html_es = post['expert_html'],
                        title_es = post['expert_comment']
                    )
                    notif_content.save()
                    last_notif_content_id = notif_content.pk
                    notifs = {}
                    goodToGo = True
                    for i in range(0, len(report_ids)):
                        report_id = report_ids[i]
                        sql = """
                            select user_id, "version_uuid" as report_id
                            from map_aux_reports a
                            where a.id = """ + report_id
                        db.execute(sql)
                        row = db.fetchall()
                        if (db.rowcount > 0):
                            public = True
                            if (post['type'] == 'private'):
                                public = False

                            notifs[i] = Notification(
                                report_id = row[0][1],
                                user_id = row[0][0],
                                expert_id = request.user.id,
                                photo_url = '',
                                acknowledged = False,
                                public = public,
                                notification_content_id = last_notif_content_id
                            )
                        else:
                            goodToGo = False

                    if goodToGo:
                        with transaction.atomic():
                            for i in notifs:
                                notifs[i].save()

                        response['success'] = True
                        response['ids'] = ', '.join(report_ids)
                        return HttpResponse(json.dumps(response, cls=DateTimeJSONEncoder),
                                    content_type='application/json')
                    else:
                        response['err'] = 'Invalid observation ID'
                        return HttpResponse(json.dumps(response, cls=DateTimeJSONEncoder),
                                content_type='application/json')

        response['err'] = 'Unauthorized yea'
        return HttpResponse(json.dumps(response, cls=DateTimeJSONEncoder),
                content_type='application/json')



@csrf_exempt
@never_cache
@cross_domain_ajax
def ajax_login(request):
    if request.method == 'POST':
        response = {'success': False, 'data': {}}
        username =  request.POST.get('username', '')
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
    response = {'success': False, 'data': {'username':'', 'groups':[], 'roles':[]}}
    success = request.user.is_authenticated()
    if success is True:
        request.session.set_expiry(86400)
        response['success'] = True
        response['data']['username'] = request.user.username
        for g in request.user.groups.all():
            response['data']['groups'].append(g.name)
        response['data']['roles'] = list(request.user.get_all_permissions())

    return HttpResponse(json.dumps(response),
                        content_type='application/json')

#from django.db import connection
class MapAuxReportsExportView(View):

    def time_filter(self, qs):
        years = self.request.GET.get('years')

        if years is not None:
            years = years.split(',')
            years_lst = []
            for i in years:
                years_lst.append(Q(observation_date__year=str(i).zfill(2)))
            qs = qs.filter(reduce(OR, years_lst))

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
        filename = 'mosquito_alert_report'
        bbox = self.request.GET.get('bbox')#caixa
        bbox = bbox.split(',') # pas necesari per obtenir valors

        #els 4 cuadrants
        southwest_lng = bbox[0]
        southwest_lat = bbox[1]
        northeast_lng = bbox[2]
        northeast_lat = bbox[3]

        qs = MapAuxReports.objects.all()

        qs = self.bbox_filter(qs)
        qs = self.time_filter(qs)
        qs = self.category_filter(qs)
        qs = qs.order_by('-observation_date')

        #Check if notification filters apply
        notifications = self.request.GET.get('notifications')
        if notifications is not None:
            MY_NOTIFICATIONS = "1"
            NOT_MY_NOTIFICATIONS = "0"

            if notifications == MY_NOTIFICATIONS:
                qs = qs.filter(version_uuid__in = Notification.objects.values('report').filter(expert = request.user.id))
            elif notifications == NOT_MY_NOTIFICATIONS:
                qs = qs.exclude(version_uuid__in = Notification.objects.values('report').filter(expert = request.user.id))

        #Check hashtag filters
        hashtag = self.request.GET.get('hashtag')
        if hashtag.lower() !='n':
            hashtag = '#' + self.request.GET.get('hashtag').replace('#','')
            qs = qs.filter(note__icontains=hashtag)

        export_type = kwargs['format']

        #Only registered users get notifications
        if authenticated is True:
            #Get observations id to check for notifications
            observations_id = qs.values_list('id', flat=True)
            #If supermosquito then get all notifications with all fields
            if request.user.groups.filter(name=superusers_group).exists():
                qs_n = Notification.objects.filter(Q(report__id__in=list(observations_id)))
                notifications_dataset = NotificationExtendedResource().export(qs_n)
            else:
                #Get registered user private notifications + anyone public notifications
                qs_n = Notification.objects.filter(
                    Q(report__id__in=list(observations_id)) &
                        ((Q(expert__id__exact = request.user.id) & Q(public__exact=0))
                        |
                        (Q(public__exact=1)) )
                    )
                notifications_dataset = NotificationResource().export(qs_n)

            #Once got the notifications, proceed
            notifications_dataset_methods = {
                'csv': notifications_dataset.csv,
                'xls': notifications_dataset.xls
            }

            response = HttpResponse(
                notifications_dataset_methods[export_type], content_type=export_type
            )

        #Continue with observations export
        if authenticated is True:
            if request.user.groups.filter(name=superusers_group).exists():
                observations_dataset = MapAuxReportsExtendedResource().export(qs)
            else:
                observations_dataset = MapAuxReportsResource().export(qs)
        else:
            observations_dataset = MapAuxReportsLimitedResource().export(qs)

        observations_dataset_methods = {
            'csv': observations_dataset.csv,
            'xls': observations_dataset.xls
        }

        response = HttpResponse(
            observations_dataset_methods[export_type], content_type=export_type
        )

        BASE_DIR = settings.BASE_DIR

        if authenticated is True:
            license_file = open(BASE_DIR + "/tigapublic/files/license.txt")
            observations_metadata_file = open(BASE_DIR + "/tigapublic/files/observations_registered_metadata.txt")
        else:
            license_file = open(BASE_DIR + "/tigapublic/files/license.and.citation.txt")
            observations_metadata_file = open(BASE_DIR + "/tigapublic/files/observations_public_metadata.txt")

        in_memory = StringIO()
        zip = ZipFile(in_memory, "a")
        zip.writestr("license.txt", license_file.read())
        zip.writestr("observations_metadata.txt", observations_metadata_file.read())
        zip.writestr("observations.xls", observations_dataset_methods[export_type])

        #Is there any notification?, only resgistered users
        if authenticated:
            if qs_n.count() >0:
                notifications_metadata_file = open(BASE_DIR + "/tigapublic/files/notifications_metadata.txt")
                zip.writestr("notifications_metadata.txt", notifications_metadata_file.read())
                zip.writestr("notifications.xls",notifications_dataset_methods[export_type]) # excel amb notificacions


        # fix for Linux zip files read in Windows
        for file in zip.filelist:
            file.create_system = 0

        zip.close()

        response = HttpResponse(mimetype="application/zip")
        response["Content-Disposition"] = "attachment; filename=mosquito_alert.zip"

        in_memory.seek(0)
        response.write(in_memory.read())

        return response



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
    #initialize default no author
    author =''
    author_in_json =''
    private_notifs =''
    public_notifs = ''
    columns = 'r.id, version_uuid, observation_date, lon,lat, ref_system, type, breeding_site_answers,mosquito_answers, expert_validated, expert_validation_result,simplified_expert_validation_result, site_cat,storm_drain_status, edited_user_notes, r.photo_url,photo_license, dataset_license, single_report_map_url,n_photos, visible, final_expert_status, private_webmap_layer'

    # IF registered user then get corresponding private notifications
    if request.user.is_authenticated():
        #Add extra columns to query
        columns = columns + ', note, t_q_1, t_q_2, t_q_3, t_a_1, t_a_2, t_a_3, s_q_1, s_q_2, s_q_3, s_q_4, s_a_1, s_a_2, s_a_3, s_a_4'

        if request.user.is_active and request.user.groups.filter(name=superusers_group).exists():
            #Set author's notification column
            author = 'au.username as author,'
            author_in_json = ',author'

            #If registered user in super-mosquito, private_notifs = all private notifs
            private_notifs = """union all
                    select """ + author + """n.report_id, nc.title_es, nc.body_html_es, n.acknowledged, TO_CHAR(n.date_comment, 'DD/MM/YYYY') as date_comment
                    from tigaserver_app_notification n, tigaserver_app_notificationcontent  nc, map_Aux_reports r, auth_user au
                    where n.public=false and n.notification_content_id = nc.id
                     and r.version_uuid = n.report_id and au.id=n.expert_id and r.id=""" + id

        else:
            #If registered user in gestors, private_notifs = get their own notifications
            if request.user.groups.filter(name=managers_group).exists():

                private_notifs = """union all
                    select """ + author + """n.report_id, nc.title_es, nc.body_html_es, n.acknowledged, TO_CHAR(n.date_comment, 'DD/MM/YYYY') as date_comment
                    from tigaserver_app_notification n , tigaserver_app_notificationcontent nc, map_Aux_reports r, auth_user au
                    where n.notification_content_id = nc.id and n.expert_id=""" + str(request.user.id) + """
                    and n.public=false and au.id=n.expert_id and r.version_uuid = n.report_id and r.id=""" + id


    #Get all public notifications regardless who made them
    public_notifs = """
        select """ + author + """n.report_id, nc.title_es, nc.body_html_es, n.acknowledged, TO_CHAR(n.date_comment, 'DD/MM/YYYY') as date_comment
        from tigaserver_app_notification n, tigaserver_app_notificationcontent  nc, map_Aux_reports r, auth_user au
        where n.public=true and n.notification_content_id = nc.id and r.version_uuid = n.report_id
        and au.id=n.expert_id and r.id=""" + id

    sql_notifs = public_notifs +' '+private_notifs

    #order all notifs desc by date_comment
    sql = """select * From (""" + sql_notifs + """ ) as f order by date_comment desc"""

    db = connection.cursor()

    sql ="""
        select json_agg((title_es, body_html_es, acknowledged, date_comment"""+author_in_json+""")) as notifs,""" + columns + """, TO_CHAR(observation_date, 'YYYYMM') AS month
            from map_aux_reports r left join (""" + sql + """) as notifs_table
        on r.version_uuid = notifs_table.report_id
        where r.id=""" + id + """
        group by """ + columns +""", TO_CHAR(observation_date, 'YYYYMM')"""


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

@cross_domain_ajax
def map_aux_reports_bounds_notifs_hashtag(request, bounds, notifs, hashtag):

    db = connection.cursor()

    res = {'num_rows': 0, 'rows': []}
    box = bounds.split(',')

    box = map(float, box)

    #CHECK notificationsjoin_hashtag = ''
    condition_notifs =''
    column_notif =''
    join_notifs =''
    if notifs.lower() != 'n':
        column_notif = ", max(e.notif) AS notif"
        condition_notifs = """, CASE n.id is null WHEN true THEN 0 ELSE
                        CASE n.expert_id = """+str(request.user.id)+""" WHEN true THEN 1
                        ELSE 0 END
                    END as notif"""
        join_notifs = """LEFT OUTER JOIN tigaserver_app_notification n
            ON (n.report_id = r.version_uuid and n.expert_id = """ + str(request.user.id)+ ") "

    #Check HASTHTAG
    join_hashtag = ''
    condition_hashtag =''
    if hashtag.lower() != 'n':
        hashtag = '#' + hashtag.replace('#','')
        join_hashtag = """ LEFT OUTER JOIN
                            map_aux_reports aux ON (r.version_uuid = aux.version_uuid)"""
        condition_hashtag = " AND aux.note ilike '%%""" + hashtag +"%%' "

    sql = """
        SELECT c, category, expert_validation_result, month, lon, lat, id """+column_notif+"""
        FROM (
            SELECT r.c, r.category, r.expert_validation_result, r.month,
            r.lon, r.lat, r.id """ + condition_notifs +"""
            FROM reports_map_data r """+ join_notifs + join_hashtag + """
            WHERE geohashlevel=8 """ + condition_hashtag + """
            AND ST_Intersects(
                ST_Point(r.lon,r.lat), ST_MakeBox2D(ST_Point(%s,%s),ST_Point(%s,%s))
            )
        ) as e
        GROUP BY c, category, expert_validation_result, month, lon, lat, id
        ORDER BY id
        """
    params = [box[0], box[1], box[2], box[3]]

    db.execute(sql, params)

    rows = dictfetchall(db)

    res['rows'] = rows
    res['num_rows'] = db.rowcount

    return HttpResponse(DateTimeJSONEncoder().encode(res),
                        content_type='application/json')


@cross_domain_ajax
def map_aux_reports_bounds_notifs(request, bounds, notifs):

    db = connection.cursor()

    res = {'num_rows': 0, 'rows': []}
    box = bounds.split(',')

    box = map(float, box)

    sql = """
        SELECT c, category, expert_validation_result, month, lon, lat, id, max(e.notif) AS notif
        FROM (
            SELECT c, category, expert_validation_result, month,
            lon, lat, r.id,
            CASE n.id is null WHEN true THEN 0 ELSE
                CASE n.expert_id = %s WHEN true THEN 1
                ELSE 0 END
            END as notif
            from reports_map_data r
            LEFT OUTER JOIN tigaserver_app_notification n ON (n.report_id = r.version_uuid and n.expert_id = %s)
            where geohashlevel=8 AND
            ST_Intersects(
                ST_Point(lon,lat), ST_MakeBox2D(ST_Point(%s,%s),ST_Point(%s,%s))
            )
        ) as e
        GROUP BY c, category, expert_validation_result, month, lon, lat, id
        ORDER BY id
        """
    params = [request.user.id, request.user.id, box[0], box[1], box[2], box[3]]

    db.execute(sql, params)

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



def notifications(request, bounds, year, months):

    db = connection.cursor()

    res = {'num_rows': 0, 'rows': []}
    box = bounds.split(',')

    # Get and prepare categories param for the sql
    # layers = categories.split(',')
    # cat = "'" + "', '".join([i for i in layers]) + "'"

    box = map(float, box)

    columns = 'a.id, a.version_uuid, a.observation_date, a.lon,a.lat, a.ref_system, a.type, a.breeding_site_answers,a.mosquito_answers, a.expert_validated, a.expert_validation_result,a.simplified_expert_validation_result, a.site_cat,a.storm_drain_status, a.edited_user_notes, a.photo_url,a.photo_license, a.dataset_license, a.single_report_map_url,a.n_photos, a.visible, a.final_expert_status, a.private_webmap_layer'

    success = request.user.is_authenticated()
    if success is True:
       columns = columns + ', a.note, a.t_q_1, a.t_q_2, a.t_q_3, a.t_a_1, a.t_a_2, a.t_a_3, a.s_q_1, a.s_q_2, a.s_q_3, a.s_q_4, a.s_a_1, a.s_a_2, a.s_a_3, a.s_a_4'


    sql = """
        select json_agg((notif.expert_comment, notif.date_comment)) as notifs, """ + columns +""", TO_CHAR(observation_date, 'YYYYMM') AS month,
           private_webmap_layer AS category
        from map_aux_reports a, tigaserver_app_notification notif
        where
        a.lon is not null and a.lat is not null
        AND
        ST_Intersects(
            ST_Point(a.lon,a.lat), ST_MakeBox2D(ST_Point(%s,%s),ST_Point(%s,%s))
        )
        and a.version_uuid = notif.report_id
    """

    # And date and layers filters to sql
    filters = ""

    if year != 'all':
        filters = " and extract(year from observation_date) = "+year

    if months != 'all':
        filters += " and extract(month from observation_date) in (" + months + ")"


    sql += filters

    sql += " GROUP BY " + columns + " ORDER BY observation_date DESC"

    # sql = "SELECT * FROM (" + sql +") as foo where category in (" + cat + ") LIMIT " + str(maxReports)

    db.execute(sql, box)
    rows = dictfetchall(db)

    res['rows'] = rows
    res['num_rows'] = len(rows)

    return HttpResponse(DateTimeJSONEncoder().encode(res),
                        content_type='application/json')


def handle_uploaded_file(request, f):
    now = datetime.datetime.now()
    filename = str(now).replace(':','_') + '_' + str(request.FILES["image"])

    with open(settings.MEDIA_ROOT + '/' + filename, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

    return filename

@csrf_exempt
@cross_domain_ajax
def imageupload(request):
    form = NotificationImageForm(request.POST, request.FILES)
    if form.is_valid():
        filename = handle_uploaded_file(request, form.cleaned_data['image'])
        model = NotificationImageFormModel(image=request.FILES["image"])
        # Copia el nom al formulari
        return HttpResponse("<script>top.$('.mce-btn.mce-open').parent().find('.mce-textbox').val('%s').closest('.mce-form').find('.mce-last.mce-formitem input:eq(0)').val('%s').parent().find('input:eq(1)').val('%s');top.$('.mce-form.mce-first > div .mce-formitem:eq(1) input').focus();top.$('.mce-notification').remove();</script>" % (settings.MEDIA_URL + filename, str(model.image.width), str(model.image.height)))
        # Copia el nom al formulari i tanca el quadre de dialeg
        return HttpResponse("<script>top.$('.mce-btn.mce-open').parent().find('.mce-textbox').val('%s').closest('.mce-window').find('.mce-primary').click();</script>" % (settings.MEDIA_URL + str(filename)))

    return HttpResponse("<script>alert('%s');</script>" % json.dumps('\n'.join([v[0] for k, v in form.errors.items()])))

@csrf_exempt
@cross_domain_ajax
def intersects(request):
    selection = request.POST.getlist('selection[]')
    nodes = []
    for i in range(0, len(selection)):
        nodes.append( selection[i] )
    nodes.append( selection[0] )
    poly = 'Polygon(( ' + (', '.join(nodes)) + ' ))'

    db = connection.cursor()
    sql = """
        select id, private_webmap_layer as category, md5(user_id) as user_id,
        to_char(observation_date, 'YYYYMM'::text) AS month
        from map_aux_reports where private_webmap_layer is not null and
        ST_Intersects(
            ST_Point(lon,lat), St_GeomFromText('"""+poly+"""')
        )
        """

    db.execute(sql)
    rows = dictfetchall(db)

    response={}
    response['success'] = True
    response['rows'] = rows
    response['num_rows'] = db.rowcount


    return HttpResponse(json.dumps(response, cls=DateTimeJSONEncoder),
        content_type='application/json')

@csrf_exempt
@cross_domain_ajax
def embornals(request):
    authenticated = request.user.is_authenticated()
    if authenticated is True:
        if request.user.is_superuser is True:
            qs = list(StormDrain.objects.values_list('lat', 'lon','water').order_by('id')) #ordered by id to assure cronological sequence
        else:
            if request.user.is_active and request.user.has_perm('tigapublic.change_stormdrain'):
                userid = request.user.id
                qs = list(StormDrain.objects.filter(user=userid).values_list('lat', 'lon','water').order_by('id')) #ordered by id to assure cronological sequence
            else:
                #No storm drain availability
                response ={}
                response['err'] = 'User with no storm drain permission'
                return HttpResponse(json.dumps(response, cls=DateTimeJSONEncoder),
                        content_type='application/json')

        return HttpResponse(json.dumps(qs), content_type='application/json')

    else:
        #No authenticated user
        response ={}
        response['err'] = 'Unauthorized'
        return HttpResponse(json.dumps(response, cls=DateTimeJSONEncoder),
                content_type='application/json')


def reports_notif(request, bounds, years, months, categories, notifications, hashtag):
    #Only registered users
    #Returns a notif column where 0->none notification of user, 1 some user notification

    db = connection.cursor()

    res = {'num_rows': 0, 'rows': []}

    #Prepare params
    box = bounds.split(',')
    box = map(float, box)
    layers = categories.split(',')
    categories = "'" + "', '".join([i for i in layers]) + "'"

    ambiguous_columns = "aux.id as id, aux.photo_url"
    columns = 'version_uuid, observation_date, lon,lat, ref_system, type, breeding_site_answers,mosquito_answers, expert_validated, expert_validation_result,simplified_expert_validation_result, site_cat,storm_drain_status, edited_user_notes, photo_license, dataset_license, single_report_map_url,n_photos, visible, final_expert_status, private_webmap_layer'

    success = request.user.is_authenticated()
    if success is True:
       columns = columns + ', note, t_q_1, t_q_2, t_q_3, t_a_1, t_a_2, t_a_3, s_q_1, s_q_2, s_q_3, s_q_4, s_a_1, s_a_2, s_a_3, s_a_4'
    else:
       return HttpResponse('Unauthorized', status=401)


    sql = """
        SELECT """ + ambiguous_columns +""",""" + columns +""", TO_CHAR(observation_date, 'YYYYMM') AS month,
            CASE n.expert_id = %s
                WHEN true THEN 1
                ELSE 0
            END as notif
        FROM map_aux_reports aux
        LEFT OUTER JOIN tigaserver_app_notification n
        ON (aux.version_uuid = n.report_id)
        WHERE
        lon is not null and lat is not null
        AND
        ST_Intersects(
            ST_Point(lon,lat), ST_MakeBox2D(ST_Point(%s,%s),ST_Point(%s,%s))
        )"""

    if hashtag.lower() not in ['none','null','n','undefined']:
        hashtag = '#' + hashtag.replace('#','')
        sql = sql + " AND note ilike '%%" + hashtag +"%%'"

    # And date and layers filters to sql
    filters = ""

    if years != 'all':
        filters = " and extract(year from observation_date) in (" + years + ")"


    if months != 'all':
        filters += " and extract(month from observation_date) in (" + months + ")"

    filters += " and private_webmap_layer in (" +categories+ ")"
    sql += filters

    sql += " ORDER BY observation_date DESC "

    sql = "SELECT id, photo_url, "+columns+", month, max(notif)as notif FROM (" + sql +") as foo group by id, photo_url," + columns + ", month"
    sql = "SELECT * FROM ("+sql+") as fooo WHERE notif = " + notifications + " LIMIT " + str(maxReports)


    db.execute(sql, [request.user.id, box[0], box[1], box[2], box[3]])
    rows = dictfetchall(db)

    res['rows'] = rows
    res['num_rows'] = len(rows)
    #res['sql']=sql

    return HttpResponse(DateTimeJSONEncoder().encode(res),
                        content_type='application/json')

def reports(request, bounds, years, months, categories, hashtag):

    db = connection.cursor()

    res = {'num_rows': 0, 'rows': []}
    box = bounds.split(',')

    # Get and prepare categories param for the sql
    layers = categories.split(',')
    cat = "'" + "', '".join([i for i in layers]) + "'"

    box = map(float, box)

    columns = 'id, version_uuid, observation_date, lon,lat, ref_system, type, breeding_site_answers,mosquito_answers, expert_validated, expert_validation_result,simplified_expert_validation_result, site_cat,storm_drain_status, edited_user_notes, photo_url,photo_license, dataset_license, single_report_map_url,n_photos, visible, final_expert_status, private_webmap_layer'

    success = request.user.is_authenticated()
    if success is True:
       columns = columns + ', note, t_q_1, t_q_2, t_q_3, t_a_1, t_a_2, t_a_3, s_q_1, s_q_2, s_q_3, s_q_4, s_a_1, s_a_2, s_a_3, s_a_4'


    sql = """
        select """ + columns +""", TO_CHAR(observation_date, 'YYYYMM') AS month,
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
    if hashtag.lower() != 'n':
        hashtag = '#' + hashtag.replace('#','')
        sql = sql + " AND note ilike '%%" + hashtag +"%%'"

    if years != 'all':
        filters = " and extract(year from observation_date) in (" + years + ")"


    if months != 'all':
        filters += " and extract(month from observation_date) in (" + months + ")"

    sql += filters

    sql += " ORDER BY observation_date DESC "

    sql = "SELECT * FROM (" + sql +") as foo where category in (" + cat + ") LIMIT " + str(maxReports)

    db.execute(sql, box)
    rows = dictfetchall(db)

    res['rows'] = rows
    res['num_rows'] = len(rows)

    return HttpResponse(DateTimeJSONEncoder().encode(res),
                        content_type='application/json')


@csrf_exempt
@never_cache
@cross_domain_ajax
#Get data for stormdrain configuration on client site. Only registered users
def getStormDrainUserSetup(request):
    if request.user.is_authenticated():
        user_id = request.user.id
    else:
        return HttpResponse('Unauthorized', status=401)

    #If super-mosquito, get list of all users and versions available
    vdic = None
    if request.user.is_active and request.user.groups.filter(name=superusers_group).exists():

        versions_available = StormDrainUserVersions.objects.extra(
            select={
                'date':'TO_CHAR(published_date, \'DD/MM/YYYY\')'
            }
        ).exclude(
            user__username__isnull=True
        ).values(
            'title', 'version','date', 'style_json', 'visible','user__username', 'user__id'
        ).order_by('-user__username').order_by('-date')

        visibleVer={}

        admin_versions = versions_available.filter(user_id__exact = user_id)
        other_versions = versions_available.exclude(user_id__exact = user_id).order_by('user_id').order_by('-version')


        vdic ={}

        #Get visible versions from super user versions
        if admin_versions.count() > 0 :
            if admin_versions[0]['style_json']:
                jstyle = json.loads(admin_versions[0]['style_json'])
                if 'users_version' in jstyle:
                    for oneStyle in jstyle['users_version']:
                        iduser = str(oneStyle['user_id'])
                        if not iduser in visibleVer:
                            visibleVer[iduser] = oneStyle['version']

        #Get visible versions from otser_versions
        if (not len(visibleVer.keys())):
            for oneVer in other_versions:
                iduser = str(oneVer['user__id'])
                if not iduser in visibleVer:
                    visibleVer[iduser] = oneVer['version']
        #return HttpResponse(json.dumps(visibleVer))
        #Get available versions for the user to choose
        if request.user.is_active and request.user.groups.filter(name=superusers_group).exists():
            for raw in other_versions:
                iduser = str(raw['user__id'])
                username = raw['user__username']
                date = raw['date']
                ver = raw['version']
                visible = raw['visible']
                title =  ( raw['title'] != None and raw['title'] ) or ''

                if not iduser in vdic:
                    version=raw['version']
                    vdic.update({iduser: {}})
                    vdic[iduser].update({
                        'username':username,
                        'visible':visibleVer[iduser],
                        'versions':[{
                            'version':ver,
                            'date':date,
                            'visible': visible,
                            'title': title
                        }]
                    })
                else:
                    vdic[iduser]['versions'].append({
                        'version':ver,
                        'date':date,
                        'visible':visible,
                        'title': title
                    })

    #Versions of the current user. This goes for all kind of users
    versions_qs = StormDrainUserVersions.objects.extra(
        select={
            'date':'TO_CHAR(published_date, \'DD/MM/YYYY\')'
        }
    ).values(
        'version','date','style_json','visible', 'title'
    ).filter(
        user__exact=user_id
    ).order_by('-version')

    #return HttpResponse(versions_qs.query)
    #Get all diferent values of each Integerfield columns.
    #Exclude null values and columns with only null values
    versions={}
    for v in versions_qs:
        versions.update({v['version']: {
            'title': (v['title'] != None and v['title']) or '',
            'date': v['date'],
            'style_json': (v['style_json'] != '' and json.loads(v['style_json'])) or '',
            'visible': v['visible']
            }})

    #fields=['water','sand']
    fields = tematic_fields

    #Check field type, to get posible operators
    foperators={}
    for field in StormDrain._meta.fields:
        #Common operators
        operators = ['=','<>']
        if field.name in tematic_fields:
            if field.get_internal_type() == 'DateTimeField':
                #Add Date operators
                operators = operators + ['<=', '>=']
            foperators.update({field.name: operators})

    res = {'versions': versions, 'fields':{}, 'operators':foperators, 'user':user_id}

    if vdic is not None:
        res['users_version'] = vdic

    for fieldname in fields:
        myFirstFilter = fieldname + '__isnull'
        mySecondFilter = fieldname + '__gt'#Used for varchar columns, avoid empty

        #For datatimefield
        if StormDrain._meta.get_field(fieldname).get_internal_type() == 'DateTimeField':
            if request.user.groups.filter(name=superusers_group).exists():
                fieldValues = StormDrain.objects.filter(
                    **{ myFirstFilter: False }
                    ).extra(
                        select={
                            'date':'TO_CHAR(date, \'YYYY/MM\')',
                            'aversion':'1' #super users have only one version to choose
                        }
                    ).values('version','user_id','date').distinct().order_by('-date')
            else:
                fieldValues = StormDrain.objects.filter(
                    **{ myFirstFilter: False }
                    ).filter(
                    user__exact=user_id
                    ).extra(
                        select={
                            'date':'TO_CHAR(date, \'YYYY/MM\')'
                        }
                    ).values('version','user_id',fieldname).distinct().order_by('-'+fieldname)
        #the rest of fields
        else:
            #Supermosquito get all storm_drain points
            if request.user.groups.filter(name=superusers_group).exists():
                fieldValues = StormDrain.objects.extra(
                    select={
                        'aversion':'1' #superusers have only one version to choose
                    }
                ).filter(
                    **{ myFirstFilter: False }
                    ).values('version','user_id',fieldname).distinct().order_by(fieldname)
            else:
                fieldValues = StormDrain.objects.filter(
                    **{ myFirstFilter: False }
                    ).filter(
                    user__exact=user_id
                    ).values('version', 'user_id', fieldname).distinct().order_by(fieldname)

        if len(fieldValues):
            #Iterate queryset and create structure
            for row in fieldValues:
                version = row['version']
                value = row[fieldname]
                iduser = row['user_id']

                if not iduser in res['fields']:
                    res['fields'].update({iduser:{}})

                if not version in res['fields'][iduser]:
                    res['fields'][iduser].update({version:{}})

                if value!='':
                    if not fieldname in res['fields'][iduser][version]:
                        res['fields'][iduser][version].update({fieldname:[]})

                    res['fields'][iduser][version][fieldname].append(value)

    return HttpResponse(json.dumps(res, cls=DateTimeJSONEncoder),
        content_type='application/json')


@csrf_exempt
def putStormDrainStyle(request, ):

    res={'success':False, 'err':''}

    style_str = request.body.decode(encoding='UTF-8')
    if request.user.is_authenticated():
        user_id = request.user.id
    else:
        return HttpResponse('Unauthorized', status=401)

    #Check is a previous version exists
    qs = StormDrainUserVersions.objects.all().filter(
            user__exact=user_id
    )

    if (qs.count() == 0):
        #Is it supermosquito user?
        if not request.user.groups.filter(name=superusers_group).exists():
            res['err'] = 'No data available'
            return HttpResponse(json.dumps(res),
                            content_type='application/json')
        else:
            addStormDrainVersion(request,1) #first version
            #re-do query
            qs = StormDrainUserVersions.objects.all().filter(
                    user__exact=user_id
            )
    else:
        qs.update(visible=False)

    #save as string the style json structure and make current version visible
    dic = json.loads(style_str)
    version = dic['version_data']

    qs = StormDrainUserVersions.objects.all().filter(
            version__exact=version, user__exact=user_id
        )
    qs.update(visible=True, style_json=style_str)

    '''
    qs = StormDrainRepresentation.objects.filter(
        user__exact = user_id, version__exact=version
        )

    #Cancel previous representation for this dataset
    qs.delete()

    version = dic['version_data']
    categories = list(dic['categories'])
    n=0 #First condition is 0, so it matches position of colors array
    l=0

    #Get user isinstance
    user = AuthUser.objects.only('id').get(id=user_id)

    for i in categories:

        category = dict(i)
        color = category['color']
        catConditions = list(category['conditions'])
        for partialCondition in catConditions:
            partial = dict(partialCondition)

            field = partial['field']
            value = partial['value']
            operator = partial['operator']

            raw =StormDrainRepresentation(
                user = user,
                version = version,
                condition = n,
                key = field,
                value = value,
                operator = operator
                )
            raw.save()
        #Now it's time to save the color of this category
        raw =StormDrainRepresentation(
            user = user,
            version = version,
            condition = n,
            key = 'color',
            value = color,
            operator = '='
            )
        raw.save()
        n += 1
        '''
    res={'success':True}
    return HttpResponse(json.dumps(res),
            content_type='application/json')


@csrf_exempt
@cross_domain_ajax
def getStormDrainData(request):

    if request.user.is_authenticated():
        user_id = request.user.id
    else:
        return HttpResponse('Unauthorized', status=401)

    #Get json style structure from StormDrainUserVersions where visible
    qs = StormDrainUserVersions.objects.values(
        'version','style_json'
    ).filter(
        visible__exact=True, user__exact=user_id
    )[:1]

    user_ver_conds=None

    if qs.count()>0:
        version = qs[0]['version']
        jstyle = json.loads(qs[0]['style_json'])
        user_ver_conds=[]
        #Super mosquito users
        if ('users_version' in jstyle):
            for user_ver in jstyle['users_version']:
                if user_ver['version'] != "0":
                    c = '(user_id ='+user_ver['user_id']
                    c = c + ' and version='+user_ver['version']+')'
                    user_ver_conds.append(c)

    else:
        jstyle={'categories':[]}
        version=-1 #Get no data

    '''
    #Get representation conditions for this version data
    qs_cond = StormDrainRepresentation.objects.filter(
        user__exact=user_id
        ).filter(
        version__exact=version
        ).values(
            'key','value','operator','condition'
        ).order_by('condition')

    #Build style structure from representation conditions
    dic={}
    for one in qs_cond:
        condition = one['condition']
        key = one['key']
        value = one['value']
        operator = one['operator']

        if not condition in dic:
            if key=='color':
                dic[condition]={'color': value, 'conditions':[]}
            else:
                dic[condition]={'conditions': [{'field':key, 'value':value, 'operator':operator}]}
        else:
            if key=='color':
                dic[condition].update({'color': value})
            else:
                dic[condition]['conditions'].append({'field':key, 'value':value, 'operator':operator}) '''

    #return HttpResponse(json.dumps(dic))
    colors=[]
    cases=[]
    ends=[]
    counter=0;

    #From dict structure build conditional SQL

    for category in jstyle['categories']:

        colors.append(category['color'])
        cond=[]

        for oneCondition in category['conditions']:
            field = oneCondition['field']
            value = oneCondition['value']
            operator = oneCondition['operator']

            if StormDrain._meta.get_field(field).get_internal_type() == 'DateTimeField':
                field ='TO_CHAR(' + field + ', \'YYYY/MM\')'

            cond.append(field + operator +"'"+value.lower()+"'")

        conds = ' and '.join(cond)
        t = 'case when ('+conds+') then '+str(counter)+' else '
        ends.append(' end ')
        cases.append(t)
        counter += 1

    #Add default value -1 to the last else and close cases when ... end.
    cases = ''.join(cases) + '-1' +''.join(ends)

    #If user in supermosquito, then get all stormdrain points
    if request.user.groups.filter(name=superusers_group).exists():
        all_user_ver_conds=''
        if user_ver_conds:
            all_user_ver_conds = '(' + ' or '.join(user_ver_conds) +')'
        sql = """
        select lat, lon, """ + cases +""" as n
        from storm_drain s_d where  """ + all_user_ver_conds +""" order by date asc"""
    else:
        sql = """
        select lat, lon, """ + cases +""" as n
        from storm_drain where user_id= """ + str(user_id) + """
        and version =""" + str(version) +""" order by date asc"""


    #exclude rows where no condition applies, n=-1
    sql = "select * from ("+ sql +") as foo where n != -1"



    db = connection.cursor()
    db.execute(sql)
    rows = db.fetchall()
    res={'rows':[], 'num_rows':0, 'colors': colors,'style_json': jstyle}
    res['rows'] = rows
    res['num_rows'] = db.rowcount


    return HttpResponse(json.dumps(res,cls=DecimalEncoder),content_type='application/json')

    #return HttpResponse(sql)

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)

@csrf_exempt
@never_cache
@cross_domain_ajax
def stormDrainUpload(request, **kwargs):
    response = {'success': False, 'desc':''}
    if (request.user.is_authenticated() and
        request.user.is_active and
        request.user.groups.filter(name=managers_group).exists()):

        if request.method == 'POST':
            readDataset = Dataset()
            importDataset = Dataset()
            file = request.FILES['stormdrain-file']
            #extension required when reading xlsx
            name, extension = os.path.splitext(request.FILES['stormdrain-file'].name)
            new_data = readDataset.load(file.read(), extension[1:])

            if extension[1:].lower()=='csv':
                stormdrain_resource = StormDrainCSVResource()
            else:
                stormdrain_resource = StormDrainResource()

            #check all compulsory fields
            missingCompulsatoryHeader = False
            contentmissing=[]
            notcontentmissing=[]
            counter=0;
            compulsatoryMissing=[]

            #headers to lowercase
            fileHeaders = [x.lower() for x in readDataset.headers]
            for key, compulsatoryVariants in compulsatory_stormdrain_fields.iteritems():
                if not bool(set(compulsatoryVariants)&set(fileHeaders)):
                    missingCompulsatoryHeader = True
                    compulsatoryMissing.append(key)
                else:
                    #find out the match between columna name and model field
                    for compulsatory in compulsatoryVariants:
                        headerposition = 0
                        for header in fileHeaders:
                            if header == compulsatory:
                                readDataset.headers[headerposition] = key
                            else:
                                headerposition = headerposition + 1

            #check for optional fields and match column names with model fields
            for key, optionalVariants in optional_stormdrain_fields.iteritems():
                for optional in optionalVariants:
                    headerposition = 0
                    for header in fileHeaders:
                        if header == optional:
                            readDataset.headers[headerposition] = key
                        else:
                            headerposition = headerposition + 1

            if not missingCompulsatoryHeader:
                #Add needed columns that aren't present in the readDataset

                readDataset.insert_col(0, col=[request.user.id,]*readDataset.height, header="user_id")
                #readDataset.insert_col(0, col=["",]*readDataset.height, header="id")

                #Prepare new version
                last_ver = getStormDrainLastVersion(request)

                readDataset.insert_col(0, col=[last_ver+1,]*readDataset.height, header="version")
                #Define index position of headers
                headers = {k: v for v, k in enumerate(readDataset.headers)}
                #Add original lat, lon columns
                readDataset.append_col(readDataset.get_col(headers['lon']), header="original_lon")
                readDataset.append_col(readDataset.get_col(headers['lat']), header="original_lat")

                importDataset.headers = readDataset.headers

                inProj = Proj(init='epsg:25831')
                outProj = Proj(init='epsg:4326')

                booleans =[]
                numerics=[]

                for field in StormDrain._meta.fields:
                    if field.get_internal_type() == 'BooleanField':
                        booleans.append(field.name)
                    elif field.get_internal_type() in ['FloatField', 'DecimalField', 'IntegerField']:
                        numerics.append(field.name)

                for row in readDataset.dict:

                    row['lon'],row['lat'] = transform(inProj,outProj,row['lon'],row['lat'])
                    #Check numeric fields. No value raises an error
                    for field in numerics:
                        if field in row:
                            row[field] = row[field] if (row[field] not in ['',None]) else 0

                    #Check boolean fields
                    for field in booleans:
                        if field in row:
                            row[field] = 'null' if row[field] == None else (
                                1 if str(row[field]).lower() in true_values else (
                                0 if str(row[field]).lower() in false_values else None))

                    new = []
                    for key in row:
                        new.append(row[key])

                    importDataset.append(new)

                db = connection.cursor()
                importDataset.headers = None

                with tempfile.NamedTemporaryFile() as f:
                    f.write(importDataset.csv)
                    f.seek(0)

                    try:
                        db.copy_from(f, 'storm_drain', columns=(readDataset.headers), sep=",", null='null')
                        nv = addStormDrainVersion(request, last_ver+1)
                        response = {'success':True, 'headers': readDataset.headers}
                    except Exception as e:
                        error = str(e).replace('\n', ' ').replace('\r', '')
                        response = {'success':False, 'err': error}

                '''
                if ( stormdrain_resource.import_data(readDataset, dry_run=False, raise_errors=True) ): # Actually import now
                    nv = addStormDrainVersion(request, last_ver+1)
                    response = {'success':True, 'File': name, 'headers': readDataset.headers}
                else:
                    response = {'success':False, 'err': name, 'File': name, 'headers': readDataset.headers}
                '''
            else:
                txtMissing = ', '.join(compulsatoryMissing)
                response = {'success':False, 'err': 'Missing compulsatory field ('+txtMissing+')'}
        else:
            response = {'success': False, 'err':'No uploaded file'}
    else:
        response = {'success': False, 'err':'Unauthorized'}

    return HttpResponse(json.dumps(response),content_type='application/json')

def getStormDrainLastVersion(request):
    #Return the last uploaded version.0 if there is none
    if request.user.is_authenticated():
        qs = StormDrain.objects.filter(
            user__exact=request.user.id, version__isnull=False
        ).values_list('version', flat=True).distinct().order_by('-version')

        if qs.count() > 0:
            version = qs.count()
        else:
            version = 0
    else:
        version = -1

    return version

def addStormDrainVersion(request, version_id=None):
    if request.user.is_authenticated():
        if version_id==None:
            version_id = getStormDrainLastVersion(request) +1

        defaultStyle = '{"version_data":"'+str(version_id)+'","categories":[{"color":"#ff0000","conditions":[{"field":"water","value":"true","operator":"="}]}]}'

        #previous versions = not visible
        qs = StormDrainUserVersions.objects.all().filter(
                user__exact=request.user.id
            )
        qs.update(visible=False)

        #Get user isinstance
        user = AuthUser.objects.only('id').get(id=request.user.id)

        #Add new version, visible
        new =StormDrainUserVersions(
            user = user,
            version = version_id,
            published_date = datetime.datetime.now(),
            #Default style
            style_json = defaultStyle,
            visible = True,
            title = request.POST.get('title', '')
            )
        new.save()
        return version_id
    else:
        return 0


def getStormDrainTemplate(request):
    success = request.user.is_authenticated()

    if success and (request.user.groups.filter(name=managers_group).exists()
        or request.user.groups.filter(name=superusers_group).exists() ):

        BASE_DIR = settings.BASE_DIR

        in_memory = StringIO()
        zip = ZipFile(in_memory, "a")

        for dirname, subdirs, files in os.walk(stormdrain_templates_path):
            #zip.write(dirname)
            for filename in files:
                zip.write(os.path.join(dirname, filename), filename)
        zip.close()

        response = HttpResponse(mimetype="application/zip")
        response["Content-Disposition"] = "attachment; filename=mosquito_alert_template.zip"

        in_memory.seek(0)
        response.write(in_memory.read())

        return response
    else:
        return HttpResponse('Unauthorized', status=401)
