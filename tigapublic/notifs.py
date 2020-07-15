"""VIEWS."""
# -*- coding: utf-8 -*-
import copy
import datetime
import decimal
import json
import os
import sys
import tempfile
import urllib
from datetime import date
from HTMLParser import HTMLParser
from operator import __or__ as OR
from StringIO import StringIO
from zipfile import ZipFile

import requests
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db import connection, transaction
from django.db.models import Q
from django.http import HttpResponse
from django.utils.html import strip_tags
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from pyproj import Proj, transform
from tablib import Dataset

from constants import (compulsatory_stormdrain_fields, false_values,
                       managers_group, maxReports, null_values,
                       optional_stormdrain_fields, stormdrain_templates_path,
                       superusers_group, tematic_fields, true_values)
from dbutils import dictfetchall
from decorators import cross_domain_ajax
from forms import NotificationImageForm
from jsonutils import DateTimeJSONEncoder
from models import (AuthUser, MapAuxReports, Municipalities, Notification,
                    NotificationContent, PredefinedNotification,
                    ObservationNotifications, ReportsMapData, StormDrain,
                    StormDrainUserVersions, UserMunicipalities)
from resources import (MapAuxReportsExtendedResource,
                       MapAuxReportsLimitedResource, MapAuxReportsResource,
                       NotificationExtendedResource, NotificationResource)

reload(sys)
sys.setdefaultencoding('utf-8')

# class Struct:
#    """Struct."""
#
#    def __init__(self, **entries):
#        """Constructor."""
#        self.__dict__.update(entries)


class UserMethods(User):
    """Custom User Methods."""

    def is_valid(self):
        """Return True if user is valid.

        A valid user is an authenticated and active user.
        """
        return self.is_authenticated() and self.is_active

    def is_manager(self):
        """Return True if user is manager.

        A manager must be valid and belong to the managers_group.
        """
        return (self.is_valid() and
                self.groups.filter(name=managers_group).exists())

    def is_root(self):
        """Return True if user is root/superadmin.

        A root must be valid and belong to the superusers_group.
        """
        return (self.is_valid() and
                self.groups.filter(name=superusers_group).exists())

    class Meta:
        """Meta."""

        proxy = True


def extendUser(user):
    """Return a User with extended methods."""
    return UserMethods.objects.get(pk=user.id)


def userIsValid(user):
    """Return True if user is valid.

    A valid user is an active & authenticated user.
    """
    return user.is_authenticated() and user.is_active


def userIsManager(user):
    """Return True if user is manager.

    A manager must be valid and belong to the managers_group.
    """
    return (userIsValid(user) and
            user.groups.filter(name=managers_group).exists())


def userIsRoot(user):
    """Return True if user is root.

    A root must be valid and belong to the superusers_group.
    """
    return (userIsValid(user) and
            user.groups.filter(name=superusers_group).exists())


class NotificationManager(View):
    """Notification Manager Class."""

    response = {'success': False}
    data = {'goodToGo': True, 'notifs': {}, 'usernotifs': {}}

    def __init__(self, request):
        """Constructor."""
        request.user = extendUser(request.user)
        self.request = request

    def userHasPrivileges(self):
        """Return True if user can send notifications."""
        return (self.request.user.is_manager() or self.request.user.is_root())

    def _saveNotificationContent(self):
        """Save the notification content."""
        notif_content = NotificationContent(
            body_html_es=self.request.POST.get('expert_html'),
            title_es=self.request.POST.get('expert_comment')
        )
        notif_content.save()
        return notif_content

    def _getPresetNotificationId(self):
        """Get the Id of the preset notification, if any."""
        preset_id = self.request.POST.get('preset_notification_id')
        if preset_id in ['', '0']:
            return None
        else:
            return PredefinedNotification.objects.get(id=preset_id)

    def _saveNotification(self, content_id):
        """Save notifications."""
        report_ids = self.request.POST.getlist('report_ids[]')
        distinctUsers = []
        preset_instance = self._getPresetNotificationId()
        for i in range(0, len(report_ids)):
            report_id = report_ids[i]
            row = MapAuxReports.objects.filter(
                    id=report_id).values('user_id', 'version_uuid')
            if row.count() > 0:
                public = (True if self.request.POST.get('type') != 'private'
                          else False)
                user = row[0]['user_id']
                if user not in distinctUsers:
                    distinctUsers.append(user)
                    self.data['usernotifs'][i] = Notification(
                        report_id=row[0]['version_uuid'],
                        user_id=user,
                        expert_id=self.request.user.id,
                        acknowledged=False,
                        public=public,
                        notification_content_id=content_id
                    )

                self.data['notifs'][i] = ObservationNotifications(
                    report_id=row[0]['version_uuid'],
                    user_id=user,
                    expert_id=self.request.user.id,
                    preset_notification=preset_instance,
                    public=public,
                    notification_content_id=content_id
                )
            else:
                self.data['goodToGo'] = False

    def _sendPushNotification(self, usernotif):
        """Send a push notification."""
        content = NotificationContent.objects.get(
                    pk=usernotif.notification_content_id)

        if settings.ENVIRON == 'production':
            user_id = usernotif.user_id
        else:
            # PROVES - ENVIA SEMPRE A ANTUANJOSEFF
            user_id = settings.TEST_CLIENTID

        if user_id.islower():
            # Android endpoint
            # set the url & params
            body_msg = HTMLParser()

            url = '%smsg_android/?user_id=%s&title=%s&message=%s' % (
                settings.TIGASERVER_API,
                urllib.quote(user_id, ''),
                urllib.quote(content.title_es.encode('utf8'), ''),
                urllib.quote(body_msg.unescape(strip_tags(
                    content.body_html_es)).encode('utf8'), '')
            )

        else:
            # iOS endpoint
            # get the link to this report
            # qs = MapAuxReports.objects.filter(
            #    version_uuid=usernotif.report_id)
            # qsobject = Struct(**qs.values()[0])
            # link_url = MapAuxReportsResource()
            #            .dehydrate_single_report_map_url(qsobject)
            link_url = ''
            # set the url & params
            url = '%smsg_ios/?user_id=%s&link_url=%s&alert_message=%s' % (
                settings.TIGASERVER_API,
                urllib.quote(user_id, ''),
                urllib.quote(link_url, ''),
                urllib.quote(strip_tags(content.body_html_es), '')
            )

        # Response codes
        # 400 - "Invalid parameters"
        # 404 - "Not found" . Unknown user id
        # 400 - "Token not set for user"

        response = requests.post(
            url,
            data={},
            headers={
                "Authorization": "Token %s" % (settings.TIGASERVER_API_TOKEN,)
            }
        )

        return json.loads(response.text)

    def _end(self):
        """Return result."""
        return HttpResponse(
            json.dumps(self.response, cls=DateTimeJSONEncoder),
            content_type='application/json'
            )

    def save(self):
        """Send notifications."""
        if self.request.method == 'POST' and self.userHasPrivileges():
            # Save the notification content and pass its PK to saveNotification
            self._saveNotification(self._saveNotificationContent().pk)
            if self.data['goodToGo'] is True:
                # Store push responses
                pushResponses = []
                # Save notifications
                with transaction.atomic():
                    for i in self.data['notifs']:
                        self.data['notifs'][i].save()

                    for i in self.data['usernotifs']:
                        self.data['usernotifs'][i].save()
                        # send push notification
                        push_response = self._sendPushNotification(
                            self.data['usernotifs'][i])
                        notification_id = str(self.data['usernotifs'][i].pk)
                        # append the push response
                        pushResponses.append({
                            'text': push_response,
                            'notification_id': notification_id})

                self.response['success'] = True
                self.response['ds'] = ', '.join(
                    self.request.POST.getlist('report_ids[]'))
                self.response['codes'] = pushResponses
                return self._end()

            else:
                self.response['err'] = 'Invalid observation ID'
                return self._end()

        else:
            self.response['err'] = 'Unauthorized'
            return self.__format__end()


@csrf_exempt
@never_cache
@cross_domain_ajax
def save_notification(request):
    """Save notifications to the database."""
    return NotificationManager(request).save()


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
    success = request.user.is_authenticated
    if success is True:
        request.session.set_expiry(86400)
        response['success'] = True
        response['data']['username'] = request.user.username
        for g in request.user.groups.all():
            response['data']['groups'].append(g.name)
        response['data']['roles'] = list(request.user.get_all_permissions())

    return HttpResponse(json.dumps(response),
                        content_type='application/json')


def time_filter(qs, years, months, date_start, date_end):
    """Time filter."""
    if date_start.upper() != 'N' and date_end.upper() != 'N':
        # Get Max time of date_end
        date_end = date(*map(int, date_end.split('-')))
        date_end = datetime.datetime.combine(date_end, datetime.time.max)

        qs = qs.filter(observation_date__range=(
            date_start, date_end)
        )

    else:
        if years.upper() != 'ALL':
            years = years.split(',')
            years_lst = []
            for i in years:
                years_lst.append(Q(observation_date__year=str(i).zfill(2)))
            qs = qs.filter(reduce(OR, years_lst))

        if months.upper() != 'ALL':
            months = months.split(',')
            lst = []
            for i in months:
                lst.append(Q(observation_date__month=str(i).zfill(2)))
            qs = qs.filter(reduce(OR, lst))

    return qs


def category_filter(qs, categories):
    """Category filter."""
    args = Q()
    if categories is not None:
        categories = categories.split(',')
        for c in categories:
            args.add(Q(private_webmap_layer=c), Q.OR)

    qs = qs.filter(args)
    return qs


def excludedcategory_filter(qs, categories):
    """Category filter."""
    args = Q()
    if categories is not None:
        categories = categories.split(',')
        for c in categories:
            args.add(Q(private_webmap_layer=c), Q.OR)

        qs = qs.exclude(
            id__in=MapAuxReports.objects.all().values(
                'id'
            ).filter(args))

    return qs


def bbox_filter(qs, bbox):
    """Box filter."""

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


def notification_filter(request, qs, my_notif, notif_types):
    """Apply notifications filter."""

    # If can not send, then can not filter either
    if not NotificationManager(request).userHasPrivileges():
        return qs

    elif my_notif.upper() != 'N':
            MY_NOTIFICATIONS = "1"
            NOT_MY_NOTIFICATIONS = "0"

            if my_notif == MY_NOTIFICATIONS:
                qs = qs.filter(
                    version_uuid__in=ObservationNotifications.objects.values(
                        'report'
                    ).filter(expert=request.user.id))

            elif my_notif == NOT_MY_NOTIFICATIONS:
                qs = qs.exclude(
                    version_uuid__in=ObservationNotifications.objects.values(
                        'report'
                    ).filter(expert=request.user.id))

    else:
        # check notification type filter
        if notif_types.upper() != 'N':
            notification_types = notif_types.split(',')
            qs = qs.filter(
                version_uuid__in=ObservationNotifications.objects.values(
                    'report'
                ).filter(preset_notification__in=notification_types))

    return qs


def hashtag_filter(qs, hashtag):
    """Apply filter hashtag."""
    if hashtag.upper() != 'N':
        qs = qs.filter(note__icontains=hashtag)
    return qs


def municipality_filter(request, qs, municipalities):
    """Apply municipalities filter."""
    if request.user.is_authenticated and municipalities == '0':
        if request.user.groups.filter(name=managers_group).exists():
            # All municipalities of registered user
            qs = qs.filter(
                municipality__in=Municipalities.objects.values(
                    'nombre'
                ).filter(
                    municipality_id__in=UserMunicipalities.objects.values(
                        'municipality_id'
                    ).filter(user_id__exact=int(request.user.id))
                )
            )

        elif request.user.groups.filter(name=superusers_group).exists():
            # All municipalities of spain
            qs = qs.filter(
                municipality__in=Municipalities.objects.values(
                    'nombre'
                ).filter(
                    tipo__exact='Municipio'
                )
            )

    else:
        if municipalities.upper() != 'N':
            # Only selected municipalities
            # Turn sring array to integer array
            municipalitiesArray = municipalities.split(',')
            int_array = map(int, municipalitiesArray)
            qs = qs.filter(
                municipality__in=Municipalities.objects.values(
                    'nombre'
                ).filter(
                    municipality_id__in=int_array
                )
            )

    return qs


class MapAuxReportsExportView(View):
    """Export xls files."""

    def getNotificationsData(self, qs):
        """Get Notifications file."""
        req = self.request
        if userIsValid(req.user) is True:
            # Get observations id to check for notifications
            observations_id = qs.values_list('id', flat=True)
            # If supermosquito then get all notifications with all fields
            if req.user.groups.filter(name=superusers_group).exists():
                qs_n = ObservationNotifications.objects.filter(
                    Q(report__id__in=list(observations_id))
                )
                notifications_dataset = NotificationExtendedResource().export(
                    qs_n
                )
            else:
                # Get registered user private notifs + anyone public notifs
                qs_n = ObservationNotifications.objects.filter(
                    Q(report__id__in=list(observations_id)) &
                    (
                        (Q(expert__id__exact=req.user.id) & Q(public__exact=0))
                        |
                        (Q(public__exact=1))
                     )
                    )
                notifications_dataset = NotificationResource().export(qs_n)

            if qs_n.count() > 0:
                notifications_dataset_methods = {
                    'csv': notifications_dataset.csv,
                    'xls': notifications_dataset.xls
                }
                return notifications_dataset_methods
            else:
                return False

    def getObservationsData(self, qs):
        """Get observations file."""
        req = self.request
        if userIsValid(req.user):
            if req.user.groups.filter(name=superusers_group).exists():
                observations_dataset = MapAuxReportsExtendedResource().export(
                    qs
                )
            else:
                observations_dataset = MapAuxReportsResource().export(qs)
        else:
            observations_dataset = MapAuxReportsLimitedResource().export(qs)

        observations_dataset_methods = {
            'csv': observations_dataset.csv,
            'xls': observations_dataset.xls
        }

        return observations_dataset_methods

    def getExportZipFiles(self, obs_dataset, notifs_dataset, export_type):
        """Get observations related files and zip them."""
        BASE_DIR = settings.BASE_DIR

        if userIsValid(self.request.user):
            license_file = open(BASE_DIR + "/tigapublic/files/license.txt")
            observations_metadata_file = open(
                BASE_DIR +
                "/tigapublic/files/observations_registered_metadata.txt"
            )
        else:
            license_file = open(
                BASE_DIR +
                "/tigapublic/files/license.and.citation.txt"
            )
            observations_metadata_file = open(
                BASE_DIR +
                "/tigapublic/files/observations_public_metadata.txt"
            )

        in_memory = StringIO()
        zip = ZipFile(in_memory, "a")
        zip.writestr("license.txt", license_file.read())
        zip.writestr("obs_metadata.txt",
                     observations_metadata_file.read())
        zip.writestr("observations.xls", obs_dataset[export_type])

        # Zip notification files
        if notifs_dataset:
            notifs_metadata_file = open(
                BASE_DIR + "/tigapublic/files/notifications_metadata.txt"
            )
            zip.writestr(
                "notifications_metadata.txt",
                notifs_metadata_file.read()
            )
            zip.writestr(
                "notifications.xls",
                notifs_dataset[export_type]
            )

        # fix for Linux zip files read in Windows
        for file in zip.filelist:
            file.create_system = 0
        zip.close()
        return in_memory

    def get(self, request, *args, **kwargs):
        """Get.

        Does a filter
        """
        qs = MapAuxReports.objects.all()

        # Check for date filters
        bbox = self.request.GET.get('bbox')
        categories = self.request.GET.get('categories')
        years = self.request.GET.get('years')
        months = self.request.GET.get('months')
        date_start = self.request.GET.get('date_start')
        date_end = self.request.GET.get('date_end')
        hashtag = self.request.GET.get('hashtag')
        municipalities = self.request.GET.get('municipalities')
        my_notif = self.request.GET.get('notifications')
        notif_types = self.request.GET.get('notif_types')

        # Reset date params when necessay
        if years is None:
            years = 'all'

        if months is None:
            months = 'all'

        if date_start is None or date_end is None:
            date_start = 'N'
            date_end = 'N'

        # Apply all possible filters
        qs = bbox_filter(qs, bbox)
        qs = time_filter(qs, years, months, date_start, date_end)
        qs = category_filter(qs, categories)
        qs = qs.order_by('-observation_date')
        qs = notification_filter(request, qs, my_notif, notif_types)
        qs = hashtag_filter(qs, hashtag)
        qs = municipality_filter(request, qs, municipalities)

        export_type = kwargs['format']

        # Only registered users get notifications
        notifications_dataset = self.getNotificationsData(qs)

        # Continue with observations export
        observations_dataset = self.getObservationsData(qs)

        in_memory = self.getExportZipFiles(
            observations_dataset, notifications_dataset, export_type
        )

        response = HttpResponse(content_type="application/zip")
        response["Content-Disposition"] = ("attachment;"
                                           "filename=mosquito_alert.zip")

        in_memory.seek(0)
        response.write(in_memory.read())

        return response


@cross_domain_ajax
def map_aux_reports_zoom_bounds(request, zoom, bounds):
    """Get Clustered Data to Show on Map."""
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

    qs = ReportsMapData.objects.filter(geohashlevel=hashlength,
                                       lon__gte=box[0], lon__lte=box[2],
                                       lat__gte=box[1], lat__lte=box[3])

    res['rows'] = list(qs.values('c', 'category', 'expert_validation_result',
                                 'month', 'lon', 'lat', 'id'))
    res['num_rows'] = qs.count()

    return HttpResponse(json.dumps(res, cls=DateTimeJSONEncoder),
                        content_type='application/json')


@cross_domain_ajax
def map_aux_reports(request, id):
    """Get All data Of One Observation."""
    field_names = ['id', 'version_uuid', 'observation_date', 'lon', 'lat',
                   'ref_system', 'type', 'breeding_site_answers',
                   'mosquito_answers', 'expert_validated',
                   'expert_validation_result',
                   'simplified_expert_validation_result', 'site_cat',
                   'storm_drain_status', 'edited_user_notes', 'photo_url',
                   'photo_license', 'dataset_license',
                   'single_report_map_url', 'n_photos', 'visible',
                   'final_expert_status', 'private_webmap_layer',
                   'municipality', 'notifiable']

    # IF registered user then get corresponding private notifications
    if not userIsValid(request.user):
        is_notifiable = 0
    else:
        arrayNotifs = []
        # Add some extra columns to query
        field_names.extend(['note'])

        if request.user.groups.filter(name=superusers_group).exists():
            # Super users can alwahs send a notification
            is_notifiable = 1

            # If registered user in super-mosquito get all private notifs
            qs_admin_notif = ObservationNotifications.objects.extra(
                select={'date_comment':
                            "to_Char(date_comment,'DD/MM/YYYY')"
                        }
                ).filter(
                    public=False
                ).values(
                    'expert__username', 'notification_content__body_html_es',
                    'notification_content__title_es'
            )

            #Extend arrayNotifs
            arrayNotifs.extend(list(qs_admin_notif))

        else:
            # Managers can send notification to observations inside their munis
            # If registered user in gestors,
            # private_notifs = get their own notifications
            if request.user.groups.filter(name=managers_group).exists():
                is_notifiable = UserMunicipalities.objects.filter(
                    municipality__nombre__exact=MapAuxReports.objects.filter
                    (
                        id__exact=id
                    ).values('municipality')
                ).count()

                if is_notifiable > 0:
                    is_notifiable = 1

                qs_manager_notif = ObservationNotifications.objects.extra(
                    select={'date_comment':
                                "to_Char(date_comment,'DD/MM/YYYY')"
                            }
                    ).filter(
                        report__id__exact=id
                    ).filter(
                        public=False
                    ).values(
                        'expert__username', 'notification_content__body_html_es',
                        'notification_content__title_es',
                        'date_comment'
                )
                arrayNotifs.extend(list(qs_manager_notif))

    # Get all public notifications regardless who made them
    qs_public_notif = ObservationNotifications.objects.extra(
        select={
                'date_comment':
                    "to_Char(date_comment,'DD/MM/YYYY')"
                }
        ).filter(
            report__id__exact=id,
            public=True
        ).values(
            'expert__username', 'notification_content__body_html_es',
            'notification_content__title_es',
            'date_comment'
    )
    arrayNotifs.extend(list(qs_public_notif))

    qs = MapAuxReports.objects.filter(id__exact=id).extra(
        select={
            'notifiable': is_notifiable
        }
    ).values(*field_names)

    # Add Notifs
    qs = [item for item in qs]
    qs[0].update({'notifs': arrayNotifs})

    return HttpResponse(json.dumps(list(qs), cls=DateTimeJSONEncoder),
                        content_type='application/json')



@cross_domain_ajax
def map_aux_reports_bounds(request, bounds):
    """Get Unclustered Sata to Show on Map Without Filters."""
    box = bounds.split(',')
    qs = ReportsMapData.objects.filter(geohashlevel=8,
                                       lon__gte=box[0], lon__lte=box[2],
                                       lat__gte=box[1], lat__lte=box[3])
    response = {
        'success': True,
        'rows': list(qs.values(
            'c', 'category', 'expert_validation_result',
            'month', 'lon', 'lat', 'id')
                     ),
        'num_rows': qs.count()
    }

    return HttpResponse(json.dumps(response, cls=DateTimeJSONEncoder),
                        content_type='application/json')


@cross_domain_ajax
def map_aux_reports_bounds_notifs(request, bounds, date_start, date_end,
                                  hashtag, municipalities,
                                  mynotifs, notif_types):
    """Get Unclustered Data to Show on Map With Filters."""
    # WHEN SHARING URL FROM REGISTERED USER TO PUBLIC USER
    if not userIsValid(request.user):
        mynotifs = 'N'
        notif_types = 'N'

    qs = MapAuxReports.objects.extra(
        # Some extra fields
        select={'c': 1,
                'category': 'private_webmap_layer',
                'month':
                    "to_Char(observation_date AT TIME ZONE 'UTC','YYYYMM')",
                }
        )
    qs = bbox_filter(qs, bounds)
    qs = time_filter(qs, 'all', 'all', date_start, date_end)
    qs = hashtag_filter(qs, hashtag)
    qs = municipality_filter(request, qs, municipalities)
    qs = notification_filter(request, qs, mynotifs, notif_types)

    response = {
        'success': True,
        'rows': list(qs.values(
            'c', 'category', 'expert_validation_result',
            'month', 'lon', 'lat', 'id')
                     ),
        'num_rows': qs.count()
    }

    return HttpResponse(DateTimeJSONEncoder().encode(response),
                        content_type='application/json')


def userfixes(request, years, months, dateStart, dateEnd):
    """Get Coverage Layer Info."""
    db = connection.cursor()

    sql_head = """
        SELECT
            ST_AsGeoJSON
                (ST_Expand(
                    ST_MakePoint(masked_lon + 0.025, masked_lat + 0.025)
                    ,0.025)
                ) AS geometry,
            count(*) AS n_fixes
        FROM tigaserver_app_fix
    """

    sql_foot = """
        GROUP BY masked_lon, masked_lat
        ORDER BY masked_lat, masked_lon
    """

    if dateStart.upper() != 'N' and dateEnd.upper() != 'N':
        sql = sql_head + """
            WHERE fix_time::date BETWEEN '"""+dateStart+"""' AND '"""+dateEnd+"""'
        """ + sql_foot
    else:
        if years == 'all' and months == 'all':
            sql = sql_head + sql_foot
        elif years == 'all':
            sql = sql_head + """
                WHERE extract(month FROM fix_time) IN ("""+months+""")
            """ + sql_foot
        elif months == 'all':
            sql = sql_head + """
                WHERE extract(year FROM fix_time) IN ("""+years+""")
            """ + sql_foot
        else:
            sql = sql_head + """
                WHERE extract(year FROM fix_time) IN ("""+years+""")
                AND extract(month FROM fix_time) IN ("""+months+""")
            """ + sql_foot

    db.execute(sql)

    rows = []
    for row in db.fetchall():
        data = {
            'geometry': json.loads(row[0]),
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


def handle_uploaded_file(request, f):
    """"Handle Upload File."""
    now = datetime.datetime.now()
    filename = str(now).replace(':', '_') + '_' + str(request.FILES["image"])

    with open(settings.MEDIA_ROOT + '/' + filename, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

    return filename


@csrf_exempt
@cross_domain_ajax
def imageupload(request):
    """Image Upload."""
    form = NotificationImageForm(request.POST, request.FILES)
    if form.is_valid():
        filename = handle_uploaded_file(request, form.cleaned_data['image'])
        # Copia el nom al formulari
        return HttpResponse(("<script>top.$('.mce-btn.mce-open').parent().find"
                             "('.mce-textbox').val('%s').closest('.mce-form')."
                             "find('.mce-last.mce-formitem input:eq(0)')."
                             "val('%s').parent().find('input:eq(1)')."
                             "val('%s');top.$('.mce-form.mce-first > div"
                             ".mce-formitem:eq(1) input').focus();"
                             "top.$('.mce-notification').remove();</script>" %
                             (settings.MEDIA_URL + filename, '100%', '')))

    return HttpResponse("<script>alert('%s');</script>" %
                        json.dumps('\n'.join([v[0] for k, v in
                                              form.errors.items()])
                                   )
                        )


@csrf_exempt
@cross_domain_ajax
def intersects_daterange(request, categories, date_start, date_end, hashtag,
                         municipalities, mynotifs, notif_types):
    """Get Observations Inside Polygon Using DateRange param."""
    return intersects(request,
                      categories, 'all', 'all', date_start, date_end,
                      hashtag, municipalities, mynotifs, notif_types)


@csrf_exempt
@cross_domain_ajax
def intersects_no_daterange(request, categories, years, months, hashtag,
                            municipalities, mynotifs, notif_types):
    """Get Observations Inside Polygon Without Using DateRange param."""
    return intersects(request, categories, years, months, 'N', 'N',
                      hashtag, municipalities, mynotifs, notif_types)


def doStringPolygon(coordinates):
    """doStringPolygon."""
    nodes = []
    for i in range(0, len(coordinates)):
        nodes.append(coordinates[i])

    nodes.append(coordinates[0])
    return 'Polygon((' + (', '.join(nodes)) + '))'


@csrf_exempt
@cross_domain_ajax
def intersects(request, excluded_categories, years, months,
               date_start, date_end, hashtag, municipalities,
               notif, notif_types):
    """Get Observations Inside Polygon."""
    # Only certain users can intersect
    if not userIsValid(request.user):
        response = {}
        response['success'] = False
        response['rows'] = 0
        response['num_rows'] = []
        return HttpResponse(json.dumps(response, cls=DateTimeJSONEncoder),
                            content_type='application/json')

    # Create polyton and calculate intersection
    poly = doStringPolygon(request.POST.getlist('selection[]'))
    cadena = "ST_Intersects(ST_Point(lon,lat), St_GeomFromText('%s'))" % poly
    qs = MapAuxReports.objects.extra(select={'user_id': "md5(user_id)"})
    qs = qs.extra(where=[cadena])
    qs = excludedcategory_filter(qs, excluded_categories)
    qs = time_filter(qs, years, months, date_start, date_end)
    qs = hashtag_filter(qs, hashtag)
    qs = municipality_filter(request, qs, municipalities)
    qs = notification_filter(request, qs, notif, notif_types)

    response = {
        'success': True,
        'rows': list(qs.values('id', 'user_id')),
        'num_rows': qs.count()
    }

    return HttpResponse(json.dumps(response, cls=DateTimeJSONEncoder),
                        content_type='application/json')


@csrf_exempt
@cross_domain_ajax
def embornals(request):
    """Embornals. Maybe it's unuseful."""
    if userIsValid(request.user) is True:
        if request.user.is_superuser is True:
            qs = list(StormDrain.objects.values_list(
                'lat', 'lon', 'water'
                ).order_by('id'))
        else:
            if (request.user.is_active and
                    request.user.has_perm('tigapublic.change_stormdrain')):
                    userid = request.user.id
                    qs = list(StormDrain.objects.filter(
                        user=userid
                        ).values_list(
                            'lat', 'lon', 'water'
                        ).order_by('id'))
            else:
                # No storm drain availability
                response = {}
                response['err'] = 'User with no storm drain permission'
                return HttpResponse(
                    json.dumps(response, cls=DateTimeJSONEncoder),
                    content_type='application/json'
                )

        return HttpResponse(json.dumps(qs), content_type='application/json')

    else:
        # No authenticated user
        response = {}
        response['err'] = 'Unauthorized'
        return HttpResponse(json.dumps(response, cls=DateTimeJSONEncoder),
                            content_type='application/json')


def reports_no_daterange(request, bounds, years, months, categories, hashtag,
                         municipalities, mynotifs, notif_types):
    """Get Reports with no DateRange."""
    if not userIsValid(request.user):
        mynotifs = 'N'
        notif_types = 'N'

    return reports(request, bounds, years, months, 'N', 'N', categories,
                   hashtag, municipalities, mynotifs, notif_types)


def reports_daterange(request, bounds, date_start, date_end, categories,
                      hashtag, municipalities, mynotifs, notif_types):
    """Get Reports with DateRange."""
    # WHEN SHARING URL FROM REGISTERED USER TO PUBLIC USER
    if not userIsValid(request.user):
        mynotifs = 'N'
        notif_types = 'N'

    return reports(request, bounds, 'all', 'all',
                   date_start, date_end, categories, hashtag,
                   municipalities, mynotifs, notif_types)


def reports(request, bounds, years, months, date_start, date_end, categories,
            hashtag, municipalities, notif, notif_types):
    """Get Reports."""
    field_names = ['id', 'photo_url', 'version_uuid', 'observation_date',
                   'lon', 'lat', 'ref_system', 'type', 'breeding_site_answers',
                   'mosquito_answers', 'expert_validated', 'n_photos',
                   'expert_validation_result', 'site_cat',
                   'storm_drain_status', 'private_webmap_layer',
                   'simplified_expert_validation_result', 'edited_user_notes',
                   'photo_license', 'dataset_license', 'single_report_map_url',
                   'visible', 'final_expert_status']

    if userIsValid(request.user):
        field_names.extend(['note'])

    # Apply filters
    qs = MapAuxReports.objects.all()
    qs = bbox_filter(qs, bounds)
    qs = time_filter(qs, years, months, date_start, date_end)
    qs = category_filter(qs, categories)
    qs = hashtag_filter(qs, hashtag)
    qs = municipality_filter(request, qs, municipalities)
    qs = notification_filter(request, qs, notif, notif_types)
    qs = qs.order_by('-observation_date')[:maxReports]

    response = {
        'rows': list(qs.values(*field_names)),
        'num_rows': qs.count()
    }

    return HttpResponse(DateTimeJSONEncoder().encode(response),
                        content_type='application/json')


@csrf_exempt
@never_cache
@cross_domain_ajax
# Get data for stormdrain configuration on client site. Only registered users
def getStormDrainUserSetup(request):
    """GetStormDrainUserSetup."""
    if request.user.is_authenticated:
        user_id = request.user.id
    else:
        return HttpResponse('Unauthorized', status=401)

    # If super-mosquito, get list of all users and versions available
    vdic = None
    if (request.user.is_active and request.user.groups.filter(
            name=superusers_group
            ).exists()):

        versions_available = StormDrainUserVersions.objects.extra(
            select={
                'date': 'TO_CHAR(published_date, \'DD/MM/YYYY\')'
            }
        ).exclude(
            user__username__isnull=True
        ).values(
            'title', 'version', 'date', 'style_json',
            'visible', 'user__username', 'user__id'
        ).order_by('-user__username').order_by('-date')

        visibleVer = {}

        admin_versions = versions_available.filter(user_id__exact=user_id)
        other_versions = versions_available.exclude(
            user_id__exact=user_id
            ).order_by('user_id').order_by('-version')

        vdic = {}

        # Get visible versions from super user versions
        if admin_versions.count() > 0:
            if admin_versions[0]['style_json']:
                jstyle = json.loads(admin_versions[0]['style_json'])
                if 'users_version' in jstyle:
                    for oneStyle in jstyle['users_version']:
                        iduser = str(oneStyle['user_id'])
                        if iduser not in visibleVer:
                            visibleVer[iduser] = oneStyle['version']

        # Get visible versions from otser_versions
        if (not len(visibleVer.keys())):
            for oneVer in other_versions:
                iduser = str(oneVer['user__id'])
                if iduser not in visibleVer:
                    visibleVer[iduser] = oneVer['version']
        # Get available versions for the user to choose
        if (request.user.is_active and request.user.groups.filter(
                name=superusers_group
                ).exists()):

            for raw in other_versions:
                iduser = str(raw['user__id'])
                username = raw['user__username']
                date = raw['date']
                ver = raw['version']
                visible = raw['visible']
                title = (raw['title'] is not None and raw['title']) or ''

                if iduser not in vdic:
                    version = raw['version']
                    vdic.update({iduser: {}})
                    vdic[iduser].update({
                        'username': username,
                        'visible': visibleVer[iduser],
                        'versions': [{
                            'version': ver,
                            'date': date,
                            'visible': visible,
                            'title': title
                        }]
                    })
                else:
                    vdic[iduser]['versions'].append({
                        'version': ver,
                        'date': date,
                        'visible': visible,
                        'title': title
                    })

    # Versions of the current user. This goes for all kind of users
    versions_qs = StormDrainUserVersions.objects.extra(
        select={
            'date': 'TO_CHAR(published_date, \'DD/MM/YYYY\')'
        }
    ).values(
        'version', 'date', 'style_json', 'visible', 'title'
    ).filter(
        user__exact=user_id
    ).order_by('-version')

    # Get all diferent values of each Integerfield columns.
    # Exclude null values and columns with only null values
    versions = {}
    for v in versions_qs:
        versions.update({v['version']: {
            'title': (v['title'] is not None and v['title']) or '',
            'date': v['date'],
            'style_json': (v['style_json'] != ''
                           and json.loads(v['style_json'])) or '',
            'visible': v['visible']
            }})

    fields = tematic_fields

    # Check field type, to get posible operators
    foperators = {}
    for field in StormDrain._meta.fields:
        # Common operators
        operators = ['=', '<>']
        if field.name in tematic_fields:
            if field.get_internal_type() == 'DateTimeField':
                # Add Date operators
                operators = operators + ['<=', '>=']
            foperators.update({field.name: operators})

    res = {'versions': versions, 'fields': {},
           'operators': foperators, 'user': user_id}

    if vdic is not None:
        res['users_version'] = vdic

    for fieldname in fields:
        # For datatimefield
        if (StormDrain._meta.get_field(fieldname).get_internal_type() ==
                'DateTimeField'):
            if request.user.groups.filter(name=superusers_group).exists():
                fieldValues = StormDrain.objects.extra(
                        select={
                            'date': 'TO_CHAR(date, \'YYYY/MM\')',
                            'aversion': '1'
                        }
                    ).values(
                        'version', 'user_id', 'date'
                    ).distinct().order_by('-date')

            else:
                fieldValues = StormDrain.objects.filter(
                    user__exact=user_id
                    ).extra(
                        select={
                            'date': 'TO_CHAR(date, \'YYYY/MM\')'
                        }
                    ).values(
                        'version', 'user_id', fieldname
                    ).distinct().order_by('-'+fieldname)
        # The rest of fields
        else:
            # Supermosquito get all storm_drain points
            if request.user.groups.filter(name=superusers_group).exists():
                fieldValues = StormDrain.objects.extra(
                    select={
                        'aversion': '1'
                    }
                ).values(
                    'version', 'user_id', fieldname
                ).distinct().order_by(fieldname)

            else:
                fieldValues = StormDrain.objects.filter(
                    user__exact=user_id
                    ).values(
                        'version', 'user_id', fieldname
                    ).distinct().order_by(fieldname)

        if len(fieldValues):
            # Iterate queryset and create structure
            for row in fieldValues:
                version = row['version']
                value = row[fieldname]
                iduser = row['user_id']

                if iduser not in res['fields']:
                    res['fields'].update({iduser: {}})

                if version not in res['fields'][iduser]:
                    res['fields'][iduser].update({version: {}})

                if value is None:
                    value = 'null'

                if value != '':
                    if fieldname not in res['fields'][iduser][version]:
                        res['fields'][iduser][version].update({fieldname: []})

                    res['fields'][iduser][version][fieldname].append(value)

        # Remove elements that have just one value and that value is null
        # Not for supermosquitos
        if not request.user.groups.filter(name=superusers_group).exists():
            jsonCopy = copy.deepcopy(res)
            for user in jsonCopy['fields']:
                for version in jsonCopy['fields'][user]:
                    for fieldname in jsonCopy['fields'][user][version]:
                        fname = jsonCopy['fields'][user][version][fieldname]
                        if (len(fname) == 1 and
                                fname[0] == 'null'):
                            del res['fields'][user][version][fieldname]

    return HttpResponse(json.dumps(res, cls=DateTimeJSONEncoder),
                        content_type='application/json')


@csrf_exempt
def putStormDrainStyle(request, ):
    """putStormDrainStyle."""
    res = {'success': False, 'err': ''}

    style_str = request.body.decode(encoding='UTF-8')
    if request.user.is_authenticated:
        user_id = request.user.id
    else:
        return HttpResponse('Unauthorized', status=401)

    # Check is a previous version exists
    qs = StormDrainUserVersions.objects.all().filter(
            user__exact=user_id
    )

    if (qs.count() == 0):
        # Is it supermosquito user?
        if not request.user.groups.filter(name=superusers_group).exists():
            res['err'] = 'No data available'
            return HttpResponse(json.dumps(res),
                                content_type='application/json')
        else:
            addStormDrainVersion(request, 1)
            # re-do query
            qs = StormDrainUserVersions.objects.all().filter(
                    user__exact=user_id
            )
    else:
        qs.update(visible=False)

    # Save as string the style json structure and make current version visible
    dic = json.loads(style_str)
    version = dic['version_data']

    qs = StormDrainUserVersions.objects.all().filter(
            version__exact=version, user__exact=user_id
        )
    qs.update(visible=True, style_json=style_str)

    res = {'success': True}
    return HttpResponse(json.dumps(res),
                        content_type='application/json')


@csrf_exempt
@cross_domain_ajax
def getStormDrainData(request):
    """getStormDrainData."""
    if request.user.is_authenticated:
        user_id = request.user.id
    else:
        return HttpResponse('Unauthorized', status=401)

    # Get json style structure from StormDrainUserVersions where visible
    qs = StormDrainUserVersions.objects.values(
        'version', 'style_json'
    ).filter(
        visible__exact=True, user__exact=user_id
    )[:1]

    user_ver_conds = None

    if qs.count() > 0:
        version = qs[0]['version']
        jstyle = json.loads(qs[0]['style_json'])
        user_ver_conds = []
        # Super mosquito users
        if ('users_version' in jstyle):
            for user_ver in jstyle['users_version']:
                if user_ver['version'] != "0":
                    c = '(user_id ='+user_ver['user_id']
                    c = c + ' and version='+user_ver['version']+')'
                    user_ver_conds.append(c)

    else:
        jstyle = {'categories': []}
        version = -1

    colors = []
    cases = []
    ends = []
    counter = 0

    # From dict structure build conditional SQL

    for category in jstyle['categories']:

        colors.append(category['color'])
        cond = []

        for oneCondition in category['conditions']:
            field = oneCondition['field']
            value = oneCondition['value']
            operator = oneCondition['operator']

            if (StormDrain._meta.get_field(field).get_internal_type()
                    == 'DateTimeField'):
                field = 'TO_CHAR(' + field + ', \'YYYY/MM\')'

            if value in null_values:
                if operator == '=':
                    operator = ' IS NULL '
                else:
                    operator = ' IS NOT NULL '

                cond.append(field + operator)
            else:
                cond.append(field + operator + "'" + value.lower() + "'")

        conds = ' AND '.join(cond)
        t = 'CASE WHEN ('+conds+') THEN '+str(counter)+' ELSE '
        ends.append(' END ')
        cases.append(t)
        counter += 1

    # Add default value -1 to the last else and close cases when ... end.
    cases = ''.join(cases) + '-1' + ''.join(ends)

    # If user in supermosquito, then get all stormdrain points
    if request.user.groups.filter(name=superusers_group).exists():
        all_user_ver_conds = ''

        if user_ver_conds:
            all_user_ver_conds = '(' + ' OR '.join(user_ver_conds) + ')'

        sql = """
        SELECT lat, lon, %s as n
            FROM storm_drain s_d
        WHERE  %s
            ORDER BY date asc""" % (
                cases, all_user_ver_conds
            )

    else:
        sql = """
        SELECT lat, lon, %s AS n
            FROM storm_drain
        WHERE user_id= %s AND version = %s ORDER BY date asc""" % (
            cases, user_id, version
        )

    # Exclude rows where no condition applies, n=-1
    sql = """
        SELECT *
            FROM (%s) AS foo
        WHERE n != -1""" % sql

    db = connection.cursor()

    db.execute(sql)
    rows = db.fetchall()
    res = {'rows': [], 'num_rows': 0, 'colors': colors, 'style_json': jstyle}
    res['rows'] = rows
    res['num_rows'] = db.rowcount

    return HttpResponse(json.dumps(res, cls=DecimalEncoder),
                        content_type='application/json')


class DecimalEncoder(json.JSONEncoder):
    """DecimalEncoder."""

    def default(self, o):
        """Turn it to decimal."""
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)


@csrf_exempt
@never_cache
@cross_domain_ajax
def stormDrainUpload(request, **kwargs):
    """stormDrainUpload."""
    response = {'success': False, 'desc': ''}
    if (userIsValid(request.user) and
            request.user.groups.filter(name=managers_group).exists()):

        if request.method == 'POST':
            readDataset = Dataset()
            importDataset = Dataset()

            # extension required when reading xlsx
            name, extension = os.path.splitext(
                request.FILES['stormdrain-file'].name
            )

            # Check all compulsory fields
            missingCompulsatoryHeader = False
            compulsatoryMissing = []

            # headers to lowercase
            fileHeaders = [x.lower() for x in readDataset.headers]
            for key, compulsatoryVariants in (
                    compulsatory_stormdrain_fields.iteritems()):

                if not bool(set(compulsatoryVariants) & set(fileHeaders)):
                    missingCompulsatoryHeader = True
                    compulsatoryMissing.append(key)
                else:
                    # find out the match between columna name and model field
                    for compulsatory in compulsatoryVariants:
                        headerposition = 0
                        for header in fileHeaders:
                            if header == compulsatory:
                                readDataset.headers[headerposition] = key
                            else:
                                headerposition = headerposition + 1

            # Check optional fields and match column names with model fields
            for key, optionalVariants in (
                    optional_stormdrain_fields.iteritems()):

                for optional in optionalVariants:
                    headerposition = 0
                    for header in fileHeaders:
                        if header == optional:
                            readDataset.headers[headerposition] = key
                        else:
                            headerposition = headerposition + 1

            if not missingCompulsatoryHeader:
                # Add needed columns that aren't present in the readDataset
                user_id = request.user.id
                readDataset.insert_col(0,
                                       col=[user_id, ]*readDataset.height,
                                       header="user_id")

                # Prepare new version
                last_ver = getStormDrainLastVersion(request)
                readDataset.insert_col(0,
                                       col=[last_ver+1, ]*readDataset.height,
                                       header="version")

                # Define index position of headers
                headers = {k: v for v, k in enumerate(readDataset.headers)}
                # Add original lat, lon columns
                readDataset.append_col(readDataset.get_col(headers['lon']),
                                       header="original_lon")
                readDataset.append_col(readDataset.get_col(headers['lat']),
                                       header="original_lat")

                importDataset.headers = readDataset.headers

                inProj = Proj(init='epsg:25831')
                outProj = Proj(init='epsg:4326')

                booleans = []
                numerics = []

                for field in StormDrain._meta.fields:
                    if field.get_internal_type() == 'NullBooleanField':
                        booleans.append(field.name)
                    elif field.get_internal_type() in [
                                'FloatField',
                                'DecimalField',
                                'IntegerField'
                            ]:
                        numerics.append(field.name)

                for row in readDataset.dict:
                    row['lon'], row['lat'] = transform(inProj,
                                                       outProj,
                                                       row['lon'],
                                                       row['lat'])
                    # Check numeric fields. No value raises an error
                    for field in numerics:
                        if field in row:
                            row[field] = row[field] if (
                                            row[field] not in ['', None]
                                        ) else 0

                    # Check boolean fields
                    for field in booleans:
                        if field in row:
                            row[field] = 'null' if row[field] is None else (
                                1 if str(row[field]).lower() in (
                                            true_values
                                ) else (
                                    0 if str(row[field]).lower() in (
                                            false_values
                                        ) else None
                                )
                            )

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
                        db.copy_from(f, 'storm_drain',
                                     columns=(readDataset.headers),
                                     sep=",",
                                     null='null')
                        addStormDrainVersion(request, last_ver+1)
                        response = {'success': True,
                                    'headers': readDataset.headers}
                    except Exception as e:
                        error = str(e).replace('\n', ' ').replace('\r', '')
                        response = {'success': False, 'err': error}

            else:
                fname = ', '.join(compulsatoryMissing)
                response = {'success': False,
                            'err': 'Missing compulsatory field (' + fname + ')'
                            }
        else:
            response = {'success': False, 'err': 'No uploaded file'}
    else:
        response = {'success': False, 'err': 'Unauthorized'}

    return HttpResponse(json.dumps(response),
                        content_type='application/json')


def getStormDrainLastVersion(request):
    """getStormDrainLastVersion."""
    # Return the last uploaded version.0 if there is none
    if request.user.is_authenticated:
        qs = StormDrain.objects.values(
            'version'
        ).filter(
            user__exact=request.user.id, version__isnull=False
        ).distinct().order_by('-version')

        if qs.count() > 0:
            version = qs[0]['version']
        else:
            version = 0
    else:
        version = -1

    return version


def addStormDrainVersion(request, version_id=None):
    """addStormDrainVersion."""
    if request.user.is_authenticated:
        if version_id is None:
            version_id = getStormDrainLastVersion(request) + 1

        defaultStyle = """{"version_data": "%s",
                         "categories":[{
                                "color":"#ff0000",
                                "conditions":[
                                    {"field": "water",
                                    "value": "true",
                                    "operator": "="}
                                ]
                            }]}""" % version_id

        # Previous versions = not visible
        qs = StormDrainUserVersions.objects.all().filter(
                user__exact=request.user.id
            )
        qs.update(visible=False)

        # Get user isinstance
        user = AuthUser.objects.only('id').get(id=request.user.id)

        # Add new version, visible
        new = StormDrainUserVersions(
            user=user,
            version=version_id,
            published_date=datetime.datetime.now(),
            # Default style
            style_json=defaultStyle,
            visible=True,
            title=request.POST.get('title', '')
            )
        new.save()
        return version_id
    else:
        return 0


def getStormDrainTemplate(request):
    """getStormDrainTemplate."""
    if (userIsValid(request.user) and
            (
                request.user.groups.filter(name=managers_group).exists()
                or request.user.groups.filter(name=superusers_group).exists()
            )):

        in_memory = StringIO()
        zip = ZipFile(in_memory, "a")

        for dirname, subdirs, files in os.walk(stormdrain_templates_path):
            # zip.write(dirname)
            for filename in files:
                zip.write(os.path.join(dirname, filename), filename)
        zip.close()

        response = HttpResponse(content_type="application/zip")
        response["Content-Disposition"] = ("attachment;filename="
                                           "mosquito_alert_template.zip")

        in_memory.seek(0)
        response.write(in_memory.read())

        return response
    else:
        return HttpResponse('Unauthorized', status=401)


@csrf_exempt
@never_cache
@cross_domain_ajax
def getPredefinedNotifications(request):
    """getPredefinedNotifications."""
    if (userIsValid(request.user) and (
            request.user.groups.filter(name=managers_group).exists()
            or request.user.groups.filter(name=superusers_group).exists()
            )):

        res = {'success': False, 'notifications': []}

        qs = PredefinedNotification.objects.filter(
            user__exact=request.user.id
            ).values(
                'id', 'title_es', 'title_ca', 'title_en',
                'body_html_es', 'body_html_ca', 'body_html_en'
            )

        for row in qs:

            res['notifications'].append({
                    'id': row['id'], 'content': {
                        'ca': {'title': row['title_ca'],
                               'body': row['body_html_ca']},
                        'es': {'title': row['title_es'],
                               'body': row['body_html_es']},
                        'en': {'title': row['title_en'],
                               'body': row['body_html_en']}
                    }})

        res['success'] = True
        return HttpResponse(json.dumps(res, cls=DateTimeJSONEncoder),
                            content_type='application/json')
    else:
        return HttpResponse('Unauthorized', status=401)


@csrf_exempt
@never_cache
@cross_domain_ajax
def getListNotifications(request):
    """getListNotifications."""
    res = {'success': False, 'notifications': []}

    if userIsValid(request.user):
        iduser = request.user.id
        if (request.user.groups.filter(name=managers_group).exists()):
            qs = PredefinedNotification.objects.filter(
                user__exact=request.user.id
                ).values(
                    'id', 'title_es', 'title_ca', 'title_en',
                    'body_html_es', 'body_html_ca', 'body_html_en',
                    'user', 'user__username'
                )
        elif (request.user.groups.filter(name=superusers_group).exists()):
                qs = PredefinedNotification.objects.values(
                        'id', 'title_es', 'title_ca', 'title_en',
                        'body_html_es', 'body_html_ca', 'body_html_en',
                        'user', 'user__username'
                    )

        for row in qs:
            res['notifications'].append(
                {'notificationid': row['id'],
                 'userid': iduser,
                 'username': row['user__username'],
                 'content': {
                    'ca': {'title': row['title_ca'],
                           'body': row['body_html_ca']},
                    'es': {'title': row['title_es'],
                           'body': row['body_html_es']},
                    'en': {'title': row['title_en'],
                           'body': row['body_html_en']}
                }}
            )

        # Uncomment to add not predifined notifications
        '''
        res['notifications'].append(
            {'notificationid': 0,
            'userid':iduser,
            'username': row['user__username'], 'content':{
                'ca': {'title':'usernotification.not-predefined', 'body':''},
                'es': {'title':'usernotification.not-predefined', 'body':''},
                'en': {'title':'usernotification.not-predefined', 'body':''}
            }}
        )
        '''

        res['success'] = True
        return HttpResponse(json.dumps(res, cls=DateTimeJSONEncoder),
                            content_type='application/json')
    else:
        return HttpResponse('Unauthorized', status=401)


@csrf_exempt
@cross_domain_ajax
def getMunicipalities(request, search):
    """getMunicipalities."""
    search_qs = Municipalities.objects.filter(
            nombre__istartswith=request.GET['query']
        ).filter(
            tipo__exact='Municipio'
        ).distinct().order_by('nombre')[:20]

    results = []
    for r in search_qs:
        # Javascript autoco  mplete requires id, text
        results.append({
            'id': str(r.municipality_id),
            'label': r.nombre
        })
    return HttpResponse(json.dumps(results, cls=DateTimeJSONEncoder),
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
        municipality_id__in=int_array
        ).distinct().order_by('nombre')

    results = {'data': []}
    for r in qs:
        # Javascript autoco  mplete requires id, text
        results['data'].append({
            'id': str(r.municipality_id),
            'label': r.nombre
        })
    return HttpResponse(json.dumps(results, cls=DateTimeJSONEncoder),
                        content_type='application/json')
