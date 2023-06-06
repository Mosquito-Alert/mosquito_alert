'''
Automatic send email script
'''
import os, sys
import csv

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path + "util_scripts/")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

import logging
import datetime
from tigaserver_app.models import NotificationContent, Notification, TigaUser, SentNotification, NotificationTopic
from tigaserver_app.serializers import custom_render_notification
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from tigacrafting.messaging import generic_send_to_topic

base_folder = proj_path + 'util_scripts/survey_files_2023/'
logs_folder = base_folder + 'logs/'

SURVEY_TITLE = {
    'en': 'Want to help us?',
    'es': '¿Quieres ayudarnos?',
    'ca': 'Ens vols donar un cop de mà?',
    'nl': 'Wil je ons helpen?',
    'el': 'Θέλετε να μας βοηθήσετε;',
    'it': 'Vuoi aiutarci?'
}


def config_logging():
    logfile_name = 'surveys_sent_' + datetime.datetime.now().strftime('%d_%m_%Y_%H%M') + ".log"
    logging.basicConfig(filename=logs_folder + logfile_name, filemode='w', format='%(name)s - %(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)


def read_file_to_lines(filename):
    try:
        file1 = open(filename, 'r')
        result = file1.read().splitlines()
        file1.close()
        return result
    except FileNotFoundError:
        return []


def send_message_to_uuid(this_uuid, sender, survey_code):

    user_language = 'en'
    try:
        user = TigaUser.objects.get(pk=this_uuid)
        if len( user.user_reports.all() ) > 0:
            first_report = user.user_reports.all().order_by('-creation_time').first()
            os_language =  first_report.app_language
            if os_language in ['en', 'es', 'ca', 'nl', 'el', 'it']:
                user_language = os_language

        # 221221 - test
        # 152148 - production
        #url = 'https://mosqal.limesurvey.net/{0}?lang={1}&uuid={2}'.format(survey_code, user_language, this_uuid)
        #url_en = 'https://mosqal.limesurvey.net/{0}?lang={1}&uuid={2}'.format(survey_code, 'en', this_uuid)
        #url = 'https://mosquitoalert.limesurvey.net/{0}?lang={1}&uuid={2}'.format(survey_code, user_language, this_uuid)
        #url_en = 'https://mosquitoalert.limesurvey.net/{0}?lang={1}&uuid={2}'.format(survey_code, 'en', this_uuid)
        url = 'https://mosquitoalert.limesurvey.net/{0}?lang={1}&G02Q33={2}'.format(survey_code, user_language, this_uuid)
        url_en = 'https://mosquitoalert.limesurvey.net/{0}?lang={1}&G02Q33={2}'.format(survey_code, 'en', this_uuid)


        context = {
            'survey_link' : url,
        }

        context_en = {
            'survey_link': url_en,
        }

        body_html_en = render_to_string("tigacrafting/survey_2023/survey_en.html", context_en).replace('&amp;', '&')
        body_html_native = render_to_string("tigacrafting/survey_2023/survey_{0}.html".format( user_language ), context).replace('&amp;', '&')
        title_native = SURVEY_TITLE[user_language]
        title_en = SURVEY_TITLE['en']

        notification_label = 'survey_{0}_{1}'.format(survey_code, user_language)

        notification_content = NotificationContent(
            body_html_en=body_html_en,
            body_html_native=body_html_native,
            title_en=title_en,
            title_native=title_native,
            native_locale=user_language,
            notification_label=notification_label
        )
        notification_content.save()

        notification = Notification(expert=sender, notification_content=notification_content )
        notification.save()

        send_notification = SentNotification(sent_to_user=user, notification=notification)
        send_notification.save()
    except TigaUser.DoesNotExist:
        logging.error("User with uuid {0} does not exist, doing nothing!!".format(this_uuid))


def send_message_to_list(list_file_args):
    sender = User.objects.get(pk=38) #mosquitoalert
    config_logging()
    if len(list_file_args) != 2:
        print("Usage: send_survey_to_everyone_in_list.py listfile survey_code")
        logging.error('Incorrect arguments')
        sys.exit(0)
    filename = list_file_args[0]
    survey_code = list_file_args[1]
    uuids = read_file_to_lines( filename )
    if len(uuids) > 0:
        n_uuids = len(uuids)
        logging.debug("Start sending messages")
        logging.debug("Read {0} uuids from file {1}".format( str(n_uuids),filename ))
        i = 0
        for uuid in uuids:
            i = i + 1
            logging.debug("Sending uuid {0} of {1}".format(str(i), str(n_uuids)))
            send_message_to_uuid(uuid, sender, survey_code)
        # and finally, the reminder
        send_global_notification_reminder()
    else:
        logging.debug("No uuids in file, doing nothing")


def send_global_notification_reminder():

    notification_content = NotificationContent.objects.get(pk=1451002)
    sender = User.objects.get(pk=38)  # mosquitoalert
    topic = NotificationTopic.objects.get(pk=1)

    notification = Notification(expert=sender, notification_content=notification_content)
    notification.save()

    send_notification = SentNotification(sent_to_topic=topic, notification=notification)
    send_notification.save()

    json_notif = custom_render_notification(sent_notification=send_notification, recipìent=None, locale='en')
    push_result = generic_send_to_topic(topic_code=topic.topic_code, title=notification_content.title_en, message='', json_notif=json_notif)



if __name__ == '__main__':
    send_message_to_list(sys.argv[1:])
