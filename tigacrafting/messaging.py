from tigaserver_project import settings_local
from tigaserver_project import settings
from pyfcm import FCMNotification


def generic_send_to_topic(topic_code, title, message, json_notif=None):
    push_service = FCMNotification(api_key=settings_local.FCM_API_KEY)
    notif_id = None
    if json_notif:
        notif_id = json_notif['id']
    notif_id = str(json_notif['id'])
    data_message = {
        "notification": {
            "body": message,
            "title": title,
        },
        "click_action": "FLUTTER_NOTIFICATION_CLICK",
        "notification_id": notif_id,
        "sound": "default",
        "data": {
            "notification": {"id": notif_id}
        }
    }
    dry_run = getattr(settings_local, 'DRY_RUN_PUSH', True)
    try:
        result = push_service.notify_topic_subscribers(topic_name=topic_code, message_body=message, message_title=title, data_message=data_message, dry_run=dry_run)
        return result
    except Exception as e:
        return {'exception': str(e) }

def generic_send(recipient_token, title, message, json_notif=None):
    push_service = FCMNotification(api_key=settings_local.FCM_API_KEY)
    registration_id = recipient_token
    notif_id = None
    if json_notif:
        notif_id = str(json_notif['id'])
    data_message = {
        "notification": {
            "body": message,
            "title": title,
        },
        "click_action": "FLUTTER_NOTIFICATION_CLICK",
        "notification_id": notif_id,
        "sound": "default",
        "data": {
            "notification": {"id": notif_id}
        }
    }
    dry_run = getattr(settings_local,'DRY_RUN_PUSH',True)
    try:
        result = push_service.notify_single_device(registration_id=registration_id, message_body=message, message_title=title, data_message=data_message, dry_run=dry_run)
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
    notif_id = None
    if json_notif:
        notif_id = str(json_notif['id'])
    data_message = {
        "notification": {
            "body": message,
            "title": title,
        },
        "click_action": "FLUTTER_NOTIFICATION_CLICK",
        "notification_id": notif_id,
        "sound": "default",
        "data": {
            "notification": {"id": notif_id}
        }
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

