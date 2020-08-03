# -*- coding: utf-8 -*-
"""Notification Libraries."""
import json
import urllib.parse
# from HTMLParser import HTMLParser  PYTHON 2
from html.parser import HTMLParser

import requests
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils.html import strip_tags

from .base import BaseManager
from tigapublic.models import (MapAuxReports, Notification,
                               NotificationContent, ObservationNotifications,
                               PredefinedNotification)


class NotificationManager(BaseManager):
    """Notification Manager Class."""

    data = {'goodToGo': True, 'notifs': {}, 'usernotifs': {}}
    model = ObservationNotifications

    def user_has_privileges(self):
        """Return True if user can send notifications.

        Both root and managers can send notifications.
        """
        return self.request.user.is_authorized

    def _save_notification(self, content_id):
        """Save notifications."""
        report_ids = self.request.POST.getlist('report_ids[]')
        distinctUsers = []
        preset_instance = self._get_preset_notification_id()
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

                self.data['notifs'][i] = self.model(
                    report_id=row[0]['version_uuid'],
                    user_id=user,
                    expert_id=self.request.user.id,
                    preset_notification=preset_instance,
                    public=public,
                    notification_content_id=content_id
                )
            else:
                self.data['goodToGo'] = False

    def _save_notification_content(self):
        """Save the notification content."""
        notif_content = NotificationContent(
            body_html_es=self.request.POST.get('expert_html'),
            title_es=self.request.POST.get('expert_comment')
        )
        notif_content.save()
        return notif_content

    def _get_preset_notification_id(self):
        """Get the Id of the preset notification, if any."""
        preset_id = self.request.POST.get('preset_notification_id')
        if preset_id in ['', '0']:
            return None
        else:
            return PredefinedNotification.objects.get(id=preset_id)

    def _send_push_notification(self, usernotif):
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
                urllib.parse.quote(user_id, ''),
                urllib.parse.quote(content.title_es.encode('utf8'), ''),
                urllib.parse.quote(body_msg.unescape(strip_tags(
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
                urllib.parse.quote(user_id, ''),
                urllib.parse.quote(link_url, ''),
                urllib.parse.quote(strip_tags(content.body_html_es), '')
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

    def save(self):
        """Send notifications."""
        if self.request.method == 'POST' and self.user_has_privileges():
            # Save the notification content and pass its PK to saveNotification
            self._save_notification(self._save_notification_content().pk)
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
                        push_response = self._send_push_notification(
                            self.data['usernotifs'][i]
                        )
                        notification_id = str(self.data['usernotifs'][i].pk)
                        # append the push response
                        pushResponses.append({
                            'text': push_response,
                            'notification_id': notification_id
                        })

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
            return self._end()

    def get_predefined_templates(self, only_my_own=False):
        """Get a list of filtering options.

        Return a list of predefined notifications that can be used to filter
        out the map observations.

        Arguments:
        - only_my_own: If set to True returns only the user's predefined
            templates (even for a root user). Default = False.
        """
        # If user is not manager nor root, bail out
        if not self.request.user.is_authorized:
            return self._end_unauthorized()
        # define respnose object
        self.response = {'notifications': [], 'success': False}
        # Get all the predefined notifications
        qs = PredefinedNotification.objects.values(
                'id', 'title_es', 'title_ca', 'title_en',
                'body_html_es', 'body_html_ca', 'body_html_en',
                'user', 'user__username'
            )
        # If user is manager, get only the notifications of this user
        if self.request.user.is_manager() or only_my_own:
            qs = qs.filter(user__exact=self.request.user.id)

        for row in qs:
            self.response['notifications'].append({
                'id': row['id'],
                'userid': self.request.user.id,
                'username': row['user__username'],
                'content': {
                    'ca': {'title': row['title_ca'],
                           'body': row['body_html_ca']},
                    'es': {'title': row['title_es'],
                           'body': row['body_html_es']},
                    'en': {'title': row['title_en'],
                           'body': row['body_html_en']}
                }
            })

        self.response['success'] = True
        return self._end()

    def _get_notifications(self, **kwargs):
        """Return a list of notifications matching the kwargs."""
        # Default extra params
        extra = {'select': {
            'date_comment': "to_Char(date_comment,'DD/MM/YYYY')"
        }}
        # Capture custom extra params
        if 'extra' in kwargs and kwargs['extra'] is not None:
            # if 'select' in kwargs['extra']:
            extra['select'].update(kwargs['extra']['select'] or {})
        # Execute query
        res = self.model.objects.extra(
                select=extra['select']
            ).filter(
                public=kwargs['public']
            )

        # If we have a pk kwarg
        if 'pk' in kwargs and kwargs['pk'] is not None:
            if type(kwargs['pk']).__name__ == 'int':
                res = res.filter(report__id=kwargs['pk'])
            if type(kwargs['pk']).__name__ == 'ValuesListQuerySet':
                res = res.filter(report__id__in=kwargs['pk'])

        # If owned is True, get only notifications issued by the current user
        if 'owned' in kwargs and kwargs['owned'] is True:
            res = res.filter(expert__id=self.request.user.id)

        if 'fields' in kwargs and kwargs['fields'] is not None:
            return list(res.values(*kwargs['fields']))
        else:
            return res.values()

    def get(self, pk=None, fields=None):
        """Get all notifications from a particular observation."""
        qs = ObservationNotifications.objects.all()

        # Filter by pk
        if pk is not None:
            if type(pk).__name__ == 'int':
                pk = [pk]
            qs = qs.filter(report__id__in=list(pk))

        # If not logged, hide issuer and show only public notifs
        if not self.request.user.is_valid():
            qs = qs.extra(select={
                'expert__username': "''"
            }).filter(public=True)

        # if user is manager
        if self.request.user.is_manager():
            query = (
                (Q(expert__id=self.request.user.id) &
                 Q(public=0))
                |
                Q(public=1)
                )
            qs = qs.filter(query)

        return qs
