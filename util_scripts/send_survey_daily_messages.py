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
from tigaserver_app.models import NotificationContent, Notification, TigaUser
from django.contrib.auth.models import User
from django.template.loader import render_to_string

base_folder = proj_path + 'util_scripts/survey_files_2024/'
logs_folder = base_folder + 'logs/'

message_content = 'tigacrafting/survey_2024/dailies/'


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
    groups = ['promotion', 'neutral', 'prevention']
    languages = [ 'ca', 'en', 'es', 'nl', 'el', 'it']
    for g in groups:
        for l in languages:
            file_list = file_list + glob.glob(root_listfiles_dir + g + "_" + l + "_*")
    return file_list


def get_title( language ):
    titles = {
        'ca': 'Missatge del dia - {0}',
        'es': 'Mensaje del día - {0}',
        'en': 'Message of the day - {0}',
        'el': 'Το μήνυμα της ημέρας - {0}',
        'nl': 'Bericht van de dag - {0}',
        'it': 'Messaggio del giorno - {0}'
    }
    today = datetime.date.today().strftime('%d/%m/%Y')
    title = titles[language].format( today )
    return title


def get_message_and_title( category, language, number ):
    title = get_title(language)
    file = proj_path + 'tigacrafting/templates/' + message_content + "{0}_{1}_{2}".format(category, language, number)
    with open( file, 'r' ) as f:
        message_text = f.read()
    message_date = datetime.date.today().strftime('%d/%m/%Y')
    context = {
        'message': message_text,
        'message_date': message_date
    }
    template = message_content + "daily_{0}.html".format( language )
    message = render_to_string(template, context).replace('&amp;', '&')
    retval = {
        'title': title,
        'message': message,
        'language': language
    }
    return retval


def do_send_notification( uuid, category, language, number ):

    user = TigaUser.objects.get(pk=uuid)
    sender = User.objects.get(pk=38)  # mosquitoalert
    current_year = str(datetime.datetime.now().year)

    message_and_title = get_message_and_title(category, language, number)

    message = message_and_title['message']
    title = message_and_title['title']
    language = message_and_title['language']

    notification_label = '{0}_{1}_{2}_{3}'.format(category, language, str(number), current_year)

    notification_content = NotificationContent(
        body_html_en=message,
        body_html_native=message,
        title_en=title,
        title_native=title,
        native_locale=language,
        notification_label=notification_label
    )
    notification_content.save()

    notification = Notification(expert=sender, notification_content=notification_content)
    notification.save()
    notification.send_to_user(user=user)

def get_uuid_tokens( uuids ):
    users = TigaUser.objects.filter(user_UUID__in=uuids)
    tokens = []
    for u in users:
        if u.device_token is not None and u.device_token != '':
            tokens.append(u.device_token)
    return tokens


def send_notification_to( actual_file, category, language, number ):
    logging.debug("Extracting uuids from file {0}".format(actual_file))
    uuids = read_file_to_lines(actual_file)
    logging.debug("Read {0} uuids from file {1}".format(len(uuids), actual_file))
    for this_uuid in uuids:
        message_and_title = get_message_and_title(category, language, number)
        logging.debug("\tSending notification to uuid {0}, category {1}, language {2}, number {3}".format(this_uuid, category, language, number))
        do_send_notification( this_uuid, category, language, number )


def treat_file(actual_file):
    logging.debug("Treating file {0}...".format(actual_file))
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
    config_logging()
    logging.debug("***** START SENDING NOTIFICATIONS TO FILE LIST ******")
    logging.debug("Scanning for files in directory {0}".format( root_listfiles_dir ))
    walk_files( root_listfiles_dir )
    logging.debug("***** END SENDING NOTIFICATIONS TO FILE LIST ******")