import ssl
import json
import socket
import struct
import binascii
#import urllib2
import urllib
import json
from tigaserver_project import settings_local
from tigaserver_project import settings
from pyfcm import FCMNotification
from datetime import date, datetime
#from tigaserver_app.models import TigaUser
#from tigaserver_app.models import Notification




def stringify_date(notification):
    new_date = notification["date_comment"].isoformat()
    if new_date.endswith('+00:00'):
        new_date = new_date[:-6] + 'Z'
    notification["date_comment"] = new_date
    return notification

'''
def get_pending_messages(token):
    unread_notifications = 0
    user = TigaUser.objects.filter(device_token=token).first()
    if user is not None:
        unread_notifications = Notification.objects.filter(user=user).filter(acknowledged=False).count()
    return unread_notifications
'''

'''
def send_message_ios(token,alert_message,link_url):
    if settings.DISABLE_PUSH_IOS:
        return "DISABLED"
    else:
        cert = '/home/webuser/webapps/tigaserver/CertificatMosquito_prod.pem'
        #try:
            #unread_notifications = get_pending_messages(token)
        #except:
        unread_notifications = 0
        TOKEN = token
        PAYLOAD = {
            'aps': {
                'alert': alert_message,
                'sound': 'default',
                'link_url': link_url,
                'badge': unread_notifications
            }
        }

        # APNS development server
        #apns_address = ('gateway.sandbox.push.apple.com', 2195)
        apns_address = (settings.APNS_ADDRESS, 2195)

        # Use a socket to connect to APNS over SSL
        s = socket.socket()
        sock = ssl.wrap_socket(s, certfile=cert)
        sock.connect(apns_address)

        # Generate a notification packet
        TOKEN = binascii.unhexlify(TOKEN)
        PAYLOAD = json.dumps(PAYLOAD)
        fmt = '!cH32sH{0:d}s'.format(len(PAYLOAD))
        cmd = '\x00'
        message = struct.pack(fmt, cmd, len(TOKEN), TOKEN, len(PAYLOAD), PAYLOAD)

        response = sock.write(message)
        #print response
        sock.close()
        return response

def send_message_android(token,title, message, notification=None):
    if settings.DISABLE_PUSH_ANDROID:
        return "DISABLED"
    else:
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
            req = urllib.request.Request(url, values, headers)
            resp = urllib.request.urlopen(req)
            resp_txt = resp.read()
            return resp_txt

        except AttributeError:
            return "No app id available in config"
'''


def generic_send(recipient_token, title, message, json_notif=None):
    push_service = FCMNotification(api_key=settings_local.FCM_API_KEY)
    registration_id = recipient_token
    if json_notif:
        notification = stringify_date(json_notif)
    else:
        notification = json_notif
    data_message = {
        "message": message,
        "title": title,
        "notif": notification
    }
    dry_run = getattr(settings_local,'DRY_RUN_PUSH',True)
    try:
        result = push_service.notify_single_device(registration_id=registration_id, data_message=data_message, dry_run=dry_run)
        return result
    except Exception as e:
        return {'exception': str(e) }



def send_message_android(tokens, title, message, notification=None):
    if settings.DISABLE_PUSH_ANDROID:
        return "DISABLED"
    else:
        return generic_send(tokens,title,message,notification)


def send_message_ios(tokens, alert_message, link_url, notification=None):
    if settings.DISABLE_PUSH_IOS:
        return "DISABLED"
    else:
        return generic_send(tokens, alert_message, link_url, notification)


def generic_multiple_send(token_list, title, message, json_notif=None):
    push_service = FCMNotification(api_key=settings_local.FCM_API_KEY)
    if json_notif:
        notification = stringify_date(json_notif)
    else:
        notification = json_notif
    data_message = {
        "message": message,
        "title": title,
        "notif": notification
    }
    dry_run = getattr(settings_local,'DRY_RUN_PUSH',True)
    try:
        result = push_service.notify_multiple_devices(registration_ids=token_list, data_message=data_message, dry_run=dry_run)
        return result
    except Exception as e:
        return {'exception': str(e)}


def send_messages_android(token_list, title, message, notification=None):
    if settings.DISABLE_PUSH_ANDROID:
        return "DISABLED"
    else:
        return generic_multiple_send(token_list,title,message,notification)


def send_messages_ios(token_list, title, message, notification=None):
    if settings.DISABLE_PUSH_IOS:
        return "DISABLED"
    else:
        return generic_multiple_send(token_list,title,message,notification)

