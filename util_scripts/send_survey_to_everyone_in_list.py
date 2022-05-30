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
from tigaserver_app.models import NotificationContent, Notification, TigaUser, SentNotification
from django.contrib.auth.models import User
from django.template.loader import render_to_string

base_folder = proj_path + 'util_scripts/survey_files/'
logs_folder = base_folder + 'logs/'

SURVEY_TITLE = "Survey"


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


def send_message_to_uuid(this_uuid, sender):

    user_language = 'en'

    user = TigaUser.objects.get(pk=this_uuid)
    if len( user.user_reports.all() ) > 0:
        first_report = user.user_reports.first()
        os_language =  first_report.os_language
        if os_language in ['en','es','ca']:
            user_language = os_language

    context = {
        'survey_link' : 'https://mosqal.limesurvey.net/221221?lang={0}&uuid={1}'.format(user_language, this_uuid),
    }

    body_html_en = render_to_string("tigacrafting/survey/survey_en.html", context).replace('&amp;', '&')
    body_html_native = render_to_string("tigacrafting/survey/survey_{0}.html".format( user_language ), context).replace('&amp;', '&')

    # notification_content = NotificationContent(
    #     body_html_en=body_html_en,
    #     body_html_native=body_html_native,
    #     title_en=SURVEY_TITLE,
    #     title_native=SURVEY_TITLE,
    #     native_locale=user_language
    # )
    # notification_content.save()
    #
    # notification = Notification(expert=sender, notification_content=notification_content)
    # notification.save()
    #
    # send_notification = SentNotification(sent_to_user=user, notification=notification)
    # send_notification.save()
    print(body_html_native)


def send_message_to_list(list_file_args):
    sender = User.objects.get(pk=38) #mosquitoalert
    config_logging()
    if len(list_file_args) != 1:
        print("Usage: send_survey_to_everyone_in_list.py listfile ")
        logging.error('Incorrect arguments')
        sys.exit(0)
    filename = list_file_args[0]
    uuids = read_file_to_lines( filename )
    if len(uuids) > 0:
        logging.debug("Start sending messages")
        logging.debug("Read {0} uuids from file {1}".format( len(uuids),filename ))
        for uuid in uuids:
            send_message_to_uuid(uuid, sender)
    else:
        logging.debug("No uuids in file, doing nothing")


if __name__ == '__main__':
    send_message_to_list(sys.argv[1:])