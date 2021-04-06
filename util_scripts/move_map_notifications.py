# This script frees already validated reports. Used mainly to prepare test databases
# coding=utf-8
import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

from tigaserver_app.models import NotificationContent, Notification, SentNotification
from tigapublic.models import PredefinedNotification, ObservationNotifications

# 1-4 ca
# 5-18 es
# 19-22 ca
# 23-27 es
# 28, 30, 32, 34, 36, 38 ca
# 29, 31, 33, 35, 37 es
def get_language_by_id(id):
    if 1 <= id <= 4 or 19 <= id <= 22:
        return 'ca'
    elif 5 <= id <= 18 or 23 <= id <= 27:
        return 'es'
    else:
        if (id % 2) == 0:
            return 'ca'
        else:
            return 'es'


def move_map_notifications():
    # first, move notification content
    # key is old PredefinedNotification id
    # value is new NotificationContent id
    id_transition = {}
    predefined_notifications = PredefinedNotification.objects.all()
    # Transform predefined notifications into regular notification content
    # since we are creating new notification content, we need to keep a table of old id to new id
    for predef in predefined_notifications:
        predef_native_locale = get_language_by_id(predef.id)
        n = NotificationContent(
            body_html_en=predef.body_html_es,
            title_en=predef.title_es,
            predefined_available_to=predef.user,
            native_locale = predef_native_locale,
            body_html_native=predef.body_html_es,
            title_native=predef.title_es,
        )
        n.save()
        id_transition[predef.id] = n.id
    # Here we move the map notifications to regular notifications
    # the content id must be updated on the new notifications
    # first we do the predefined ones ...
    map_notifications_predefined = ObservationNotifications.objects.filter(preset_notification__isnull=False).all()
    for map_notif in map_notifications_predefined:
        n = Notification(
            report=map_notif.report,
            expert=map_notif.expert,
            date_comment=map_notif.date_comment,
            expert_comment='',
            expert_html='',
            public=map_notif.public,
            notification_content=id_transition[map_notif.id],
            map_notification=True
        )
        n.save()
        # and send the notifications
        sn = SentNotification(
            sent_to_user=map_notif.user_id,
            notification=n
        )
        sn.save()
    # ... then we do de not predefined
    map_notifications_not_predefined = ObservationNotifications.objects.filter(preset_notification__isnull=True).all()
    for map_notif in map_notifications_not_predefined:
        n = Notification(
            report=map_notif.report,
            expert=map_notif.expert,
            date_comment=map_notif.date_comment,
            expert_comment='',
            expert_html='',
            public=map_notif.public,
            notification_content=map_notif.id,
            map_notification=True
        )
        n.save()
        # and also send the notifications
        sn = SentNotification(
            sent_to_user=map_notif.user_id,
            notification=n
        )
        sn.save()
