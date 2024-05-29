# -*- coding: utf-8 -*-
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
from tigaserver_app.models import NotificationContent, Notification, TigaUser, NotificationTopic, AcknowledgedNotification
from django.contrib.auth.models import User
from django.template.loader import render_to_string
import message_sets as sets

base_folder = proj_path + 'util_scripts/survey_files_2024/'
logs_folder = base_folder + 'logs/'


SURVEY_TEXT_DEFAULT = sets.SET_DEFAULT

SURVEY_TEXT = {
  "6": { "3": sets.SET_1, "8": sets.SET_2, "13": sets.SET_3, "18": sets.SET_4, "23": sets.SET_5, "28": sets.SET_1, },
  "7": { "3": sets.SET_1, "8": sets.SET_2, "13": sets.SET_3, "18": sets.SET_4, "23": sets.SET_5, "28": sets.SET_1, },
  "8": { "2": sets.SET_1, "7": sets.SET_2, "12": sets.SET_3, "17": sets.SET_4, "22": sets.SET_5, "27": sets.SET_1, },
  "9": { "1": sets.SET_1, "6": sets.SET_2, "11": sets.SET_3, "16": sets.SET_4, "21": sets.SET_5, "26": sets.SET_1, },
  "10": { "1": sets.SET_1, "6": sets.SET_2, "11": sets.SET_3, "15": sets.SET_4, "20": sets.SET_5, "25": sets.SET_1, "30": sets.SET_2, }
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

def get_today_title_and_message(month,day,language):
    try:
        title_and_message = SURVEY_TEXT[ str(month) ][ str(day) ][ language ]
        return title_and_message
    except KeyError:
        return SURVEY_TEXT_DEFAULT[ language ]


def send_message_to_uuid(this_uuid, sender, survey_code):

    today = datetime.date.today()
    day = today.day
    month = today.month

    try:
        user = TigaUser.objects.get(pk=this_uuid)
        user_language = user.language_iso2 if user.language_iso2 in SURVEY_TEXT_DEFAULT.keys() else 'en'

        title_and_message_native = get_today_title_and_message(month,day,user_language)
        title_native = title_and_message_native['title']
        message_native = title_and_message_native['message']
        title_and_message_en = get_today_title_and_message(month,day,'en')
        title_en = title_and_message_en['title']
        message_en = title_and_message_en['message']

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
            'title': title_native,
            'message': message_native
        }

        context_en = {
            'survey_link': url_en,
            'title': title_en,
            'message': message_en
        }

        body_html_en = render_to_string("tigacrafting/survey_2023/survey_en.html", context_en).replace('&amp;', '&')
        body_html_native = render_to_string("tigacrafting/survey_2023/survey_{0}.html".format( user_language ), context).replace('&amp;', '&')
        title_native = title_native
        title_en = title_en

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

        notification.send_to_user(user=user)
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
        # send_global_notification_reminder()
    else:
        logging.debug("No uuids in file, doing nothing")


def score_label(score):
    if score > 66:
        return "user_score_pro"
    elif 33 < score <= 66:
        return "user_score_advanced"
    else:
        return "user_score_beginner"


def custom_render_notification(sent_notification, recipient, locale):
    expert_comment = sent_notification.notification.notification_content.get_title(language_code=locale)
    expert_html = sent_notification.notification.notification_content.get_body_html(language_code=locale)

    ack = False
    if recipient is not None:
        ack = AcknowledgedNotification.objects.filter(user=recipient,notification=sent_notification.notification).exists()

    this_content = {
        'id': sent_notification.notification.id,
        'report_id': sent_notification.notification.report.version_UUID if sent_notification.notification.report is not None else None,
        'user_id': sent_notification.sent_to_user.user_UUID if sent_notification.sent_to_user is not None else None,
        'topic': sent_notification.sent_to_topic.topic_code if sent_notification.sent_to_topic is not None else None,
        'user_score': sent_notification.sent_to_user.score if sent_notification.sent_to_user is not None else None,
        'user_score_label': score_label(sent_notification.sent_to_user.score) if sent_notification.sent_to_user is not None else None,
        'expert_id': sent_notification.notification.expert.id,
        'date_comment': sent_notification.notification.date_comment,
        'expert_comment': expert_comment,
        'expert_html': expert_html,
        'acknowledged': ack,
        'public': sent_notification.notification.public,
    }
    return this_content


def send_global_notification_reminder():

    notification_content = NotificationContent.objects.get(pk=1453086)
    sender = User.objects.get(pk=38)  # mosquitoalert
    topic = NotificationTopic.objects.get(pk=1)

    notification = Notification(expert=sender, notification_content=notification_content)
    notification.save()

    notification.send_to_topic(topic=topic)


if __name__ == '__main__':
    send_message_to_list(sys.argv[1:])
