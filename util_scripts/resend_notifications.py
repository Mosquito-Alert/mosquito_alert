# Sort of sandbox to play with APN messaging and multiple message sending
# coding=utf-8
import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

from tigaserver_app.models import Report, TigaUser, Notification
from tigaserver_project import settings_local
from tigaserver_project import settings
from tigacrafting.messaging import stringify_date, get_pending_messages
from apns import APNs, Frame, Payload
import time
import ssl
import json
import socket
import struct
import binascii
import urllib2
import json


def send_message_android(tokens,title, message, notification=None):
    try:
        app_id = settings_local.ANDROID_GCM_API_KEY
        private_keys = tokens

        url = settings.FCM_ADDRESS
        headers = {
            "Content-Type": "application/json",
            "Authorization": "key=" + app_id
        }

        if notification:
            notification = stringify_date(notification)
            values = {
                "registration_ids": private_keys,
                "collapse_key": "mosquito_alert",
                "data": {
                    "message": message,
                    "big_icon": True,
                    "title": title,
                    "notification": notification
                }
            }
        else:
            values = {
                "registration_ids": private_keys,
                "collapse_key": "mosquito_alert",
                "data": {
                    "message": message,
                    "big_icon": True,
                    "title": title
                }
            }

        values = json.dumps(values)
        req = urllib2.Request(url, values, headers)
        resp = urllib2.urlopen(req)
        resp_txt = resp.read()
        return resp_txt
    except AttributeError:
        return "No app id available in config"


def send_message_ios(tokens,alert_message,link_url):
    cert = '/home/webuser/webapps/tigaserver/CertificatMosquito_prod.pem'
    frame = Frame()
    identifier = 1
    expiry = time.time() + 3600
    priority = 10
    apns = APNs(use_sandbox=True, cert_file=cert)
    for single_token in tokens:
        try:
            unread_notifications = get_pending_messages(single_token)
        except:
            unread_notifications = 0
        payload = Payload(alert=alert_message, sound="default", badge=unread_notifications)
        frame.add_item(single_token, payload, identifier, expiry, priority)
    apns.gateway_server.send_notification_multiple(frame)


#THIS IS THE PART WHERE WE DO STUFF

notifs = Notification.objects.filter(notification_content__id=4107)
send_to_android = []
send_to_ios = []
DATA_CHUNK_LENGTH = 100

grabbed_notification_content = False
notification_content = None
title = None
message = None

for notif in notifs:
    if not grabbed_notification_content:
        notification_content = notif.notification_content
        title = notif.notification_content.title_es
        message = notif.notification_content.title_es
        grabbed_notification_content = True
    if notif.acknowledged is False and notif.user.device_token:
        if notif.user.user_UUID.islower():
            send_to_android.append(notif.user.user_UUID)
        else:
            send_to_ios.append(notif.user.user_UUID)

chunks_android = [send_to_android[x:x+DATA_CHUNK_LENGTH] for x in xrange(0,len(send_to_android),DATA_CHUNK_LENGTH)]
chunks_ios = [send_to_ios[x:x+DATA_CHUNK_LENGTH] for x in xrange(0,len(send_to_ios),DATA_CHUNK_LENGTH)]


print("Send to android " + str(len(send_to_android)))
print("Send to ios " + str(len(send_to_ios)))

print("Chunks android " + str(len(chunks_android)))
for chunk in chunks_android:
    print("Chunk android length " + str(len(chunk)))

print("Chunks ios " + str(len(chunks_ios)))
for chunk in chunks_ios:
    print("Chunk ios length " + str(len(chunk)))