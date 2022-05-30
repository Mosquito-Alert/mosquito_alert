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
import glob
from tigaserver_app.models import NotificationContent, Notification, TigaUser, SentNotification
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from tigacrafting.messaging import generic_send

base_folder = proj_path + 'util_scripts/survey_files/'
logs_folder = base_folder + 'logs/'

list_files_root = '/home/webuser/dev/python/survey_sender/test_files/roll3/'
message_content = 'tigacrafting/survey/dailies/'


def config_logging():
    logfile_name = 'dailies_sent_' + datetime.datetime.now().strftime('%d_%m_%Y_%H%M') + ".log"
    logging.basicConfig(filename=logs_folder + logfile_name, filemode='w', format='%(name)s - %(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)


def read_file_to_lines(filename):
    try:
        file1 = open(filename, 'r')
        result = file1.read().splitlines()
        file1.close()
        return result
    except FileNotFoundError:
        return []


def generate_file_list(root_listfiles_dir):
    file_list = []
    groups = ['eager', 'neutral', 'prevention']
    languages = [ 'ca', 'en', 'es' ]
    for g in groups:
        for l in languages:
            file_list = file_list + glob.glob(root_listfiles_dir + g + "_" + l + "_*")
    return file_list


def get_title( category, language, number ):
    title = "{0}_{1}_{2}".format(category, language, number)
    return title


def get_message_and_title( category, language, number ):
    title = get_title(category, language, number)
    message = render_to_string(message_content + "{0}_{1}_{2}".format(category, language, number), {}).replace('&amp;', '&')
    retval = {
        'title': title,
        'message': message,
        'language': language
    }
    return retval


def do_send_notification( uuid, message_and_title  ):

    user = TigaUser.objects.get(pk=uuid)
    sender = User.objects.get(pk=38)  # mosquitoalert

    message = message_and_title['message']
    title = message_and_title['title']
    language = message_and_title['language']

    try:
        notification_content = NotificationContent.objects.get(body_html_native=message)
    except NotificationContent.DoesNotExist:
        notification_content = NotificationContent(
            body_html_en=message,
            body_html_native=message,
            title_en=title,
            title_native=title,
            native_locale=language
        )
        notification_content.save()

    notification = Notification(expert=sender, notification_content=notification_content)
    notification.save()

    send_notification = SentNotification(sent_to_user=user, notification=notification)
    send_notification.save()

    generic_send( user.device_token, title, message )


def get_uuid_tokens( uuids ):
    users = TigaUser.objects.filter(user_UUID__in=uuids)
    tokens = []
    for u in users:
        if u.device_token is not None and u.device_token != '':
            tokens.append(u.device_token)
    return tokens


def send_notification_to( actual_file, category, language, number ):
    uuids = read_file_to_lines(actual_file)
    for this_uuid in uuids:
        message_and_title = get_message_and_title(category, language, number)
        do_send_notification( this_uuid, message_and_title )


def treat_file(actual_file):
    file_no_path = os.path.basename(actual_file)
    name_parts = file_no_path.split('_')
    category = name_parts[0]
    language = name_parts[1]
    message_number = name_parts[2]
    if message_number != 'completed':
        send_notification_to( actual_file, category, language, message_number )


def walk_files(root_listfiles_dir):
    files = generate_file_list(root_listfiles_dir)
    for actual_file in files:
        treat_file(actual_file)


if __name__ == '__main__':
    args = sys.argv[1:]
    root_listfiles_dir = args[0]
    walk_files( root_listfiles_dir )