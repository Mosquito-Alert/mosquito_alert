# This script frees already validated reports. Used mainly to prepare test databases
# coding=utf-8
import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

from tigaserver_app.models import NotificationContent, Notification, SentNotification, Report, TigaUser
from tigapublic.models import PredefinedNotification, ObservationNotifications
from django.contrib.auth.models import User
from progress.bar import Bar

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
    total_predefined = predefined_notifications.count()

    user_lookup = {}
    users = User.objects.all()
    bar = Bar('Building user lookup', max=users.count())
    for u in users:
        user_lookup[u.id] = u
        bar.next()
    bar.finish()

    report_lookup = {}
    report_ids = ObservationNotifications.objects.all().values('report__version_uuid').distinct()
    reports = Report.objects.filter(version_UUID__in=report_ids)
    bar = Bar('Building reports lookup', max=reports.count())
    for r in reports:
        report_lookup[r.version_UUID] = r
        bar.next()
    bar.finish()

    tigauser_lookup = {}
    tigausers = TigaUser.objects.all()
    bar = Bar('Building tigauser lookup', max=tigausers.count())
    for t in tigausers:
        tigauser_lookup[t.user_UUID] = t
        bar.next()
    bar.finish()

    notification_content_lookup = {}
    notification_content_ids = ObservationNotifications.objects.filter(preset_notification__isnull=True).all().values('notification_content__id').distinct()
    notification_contents = NotificationContent.objects.filter(id__in=notification_content_ids)
    bar = Bar('Building notification content lookup', max=notification_contents.count())
    for not_content in notification_contents:
        notification_content_lookup[not_content.id] = not_content
        bar.next()
    bar.finish()

    # Transform predefined notifications into regular notification content
    # since we are creating new notification content, we need to keep a table of old id to new id
    bar = Bar('Predefined notifications to regular notifications', max=predefined_notifications.count())
    for predef in predefined_notifications:
        predef_native_locale = get_language_by_id(predef.id)
        user = user_lookup[predef.user.id]
        n = NotificationContent(
            body_html_en=predef.body_html_es,
            title_en=predef.title_es,
            predefined_available_to=user,
            native_locale = predef_native_locale,
            body_html_native=predef.body_html_es,
            title_native=predef.title_es,
        )
        n.save()
        id_transition[predef.id] = n.id
        bar.next()
    bar.finish()
    # Here we move the map notifications to regular notifications
    # the content id must be updated on the new notifications
    # first we do the predefined ones ...
    map_notifications_predefined = ObservationNotifications.objects.filter(preset_notification__isnull=False).all()
    total_preset = map_notifications_predefined.count()
    bar = Bar('Processing predefined map notifs', max=total_preset)
    for map_notif in map_notifications_predefined:
        report = None
        try:
            report = report_lookup[map_notif.report_id]
        except:
            print( map_notif.report_id + " not found" )
        #user = User.objects.get(pk=map_notif.expert.id)
        user = user_lookup[map_notif.expert.id]
        notif_content = NotificationContent.objects.get(pk=id_transition[map_notif.preset_notification.id])
        #tigauser = TigaUser.objects.get(pk=map_notif.user_id)
        tigauser = tigauser_lookup[map_notif.user_id]
        if report is not None:
            n = Notification(
                report=report,
                expert=user,
                date_comment=map_notif.date_comment,
                expert_comment='',
                expert_html='',
                public=map_notif.public,
                notification_content=notif_content,
                map_notification=True
            )
            n.save()
            # and send the notifications
            sn = SentNotification(
                sent_to_user=tigauser,
                notification=n
            )
            sn.save()
        bar.next()
    bar.finish()
    # ... then we do de not predefined
    map_notifications_not_predefined = ObservationNotifications.objects.filter(preset_notification__isnull=True).all()
    total_no_preset = map_notifications_not_predefined.count()
    bar = Bar('Processing not predefined map notifs',max=total_no_preset)
    for map_notif in map_notifications_not_predefined:
        report = None
        try:
            report = report_lookup[map_notif.report_id]
        except:
            print(map_notif.report_id + " not found")
        #user = User.objects.get(pk=map_notif.expert.id)
        user = user_lookup[map_notif.expert.id]
        notif_content = None
        try:
            #notif_content = NotificationContent.objects.get(pk=map_notif.notification_content.id)
            notif_content = notification_content_lookup[map_notif.notification_content.id]
        except:
            print("NotificationContent " + str(map_notif.id) + " not found")
        # tigauser = TigaUser.objects.get(pk=map_notif.user_id)
        tigauser = tigauser_lookup[map_notif.user_id]
        if report is not None and notif_content is not None:
            n = Notification(
                report=report,
                expert=user,
                date_comment=map_notif.date_comment,
                expert_comment='',
                expert_html='',
                public=map_notif.public,
                notification_content=notif_content,
                map_notification=True
            )
            n.save()
            # and also send the notifications
            sn = SentNotification(
                sent_to_user=tigauser,
                notification=n
            )
            sn.save()
        bar.next()
    bar.finish()

move_map_notifications()