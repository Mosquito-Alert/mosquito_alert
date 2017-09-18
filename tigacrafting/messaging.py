import ssl
import time
import json
import socket
import struct
import binascii
import urllib2
import json
from tigaserver_project import settings_local
from tigaserver_project import settings
from datetime import date, datetime
from tigaserver_app.models import TigaUser
from tigaserver_app.models import Notification
from apns import APNs, Frame, Payload


def stringify_date(notification):
    new_date = notification["date_comment"].isoformat()
    if new_date.endswith('+00:00'):
        new_date = new_date[:-6] + 'Z'
    notification["date_comment"] = new_date
    return notification


def get_pending_messages(token):
    unread_notifications = 0
    user = TigaUser.objects.filter(device_token=token).first()
    if user is not None:
        unread_notifications = Notification.objects.filter(user=user).filter(acknowledged=False).count()
    return unread_notifications


def send_message_ios(token,alert_message,link_url):
    cert = '/home/webuser/webapps/tigaserver/CertificatMosquito.pem'
    try:
        unread_notifications = get_pending_messages(token)
    except:
        unread_notifications = 0

    apns = APNs(use_sandbox=True, cert_file=cert)
    token_hex = token
    payload = Payload(alert=alert_message, sound="default", badge=unread_notifications)
    apns.gateway_server.send_notification(token_hex,payload)


def send_multiple_messages_ios(token,alert_message,link_url):
    cert = '/home/webuser/webapps/tigaserver/CertificatMosquito.pem'
    frame = Frame()
    identifier = 1
    expiry = time.time() + 3600
    priority = 10
    apns = APNs(use_sandbox=True, cert_file=cert)
    for single_token in token:
        try:
            unread_notifications = get_pending_messages(token)
        except:
            unread_notifications = 0
        payload = Payload(alert=alert_message, sound="default", badge=unread_notifications)
        frame.add_item(single_token, payload, identifier, expiry, priority)
    apns.gateway_server.send_notification_multiple(frame)


def send_message_android(token,title, message, notification=None):
    try:
        #token = 'eqFkux_dIuo:APA91bGmmOxn16z8VhHE3O0tB7VmDsPX5p0xBfzJpSPi8O8gNaCbyJlJDwTdOAm4cOADCZ4KK5JRgV1NvAH_1YriYZob00Y5QCBw9FefMrpbs2pCD5TAKrkWy3vUNbwZQZGkySOqLH79'
        app_id = settings_local.ANDROID_GCM_API_KEY
        # List of device tokens to send the message to. Can be 1 item
        private_keys = [token]
        #private_keys.append(token)

        #url = "https://android.googleapis.com/gcm/send"
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
