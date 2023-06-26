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
from tigaserver_app.models import NotificationContent, Notification, TigaUser, SentNotification, NotificationTopic, AcknowledgedNotification
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from tigacrafting.messaging import generic_send_to_topic
from tigacrafting.messaging import generic_send

base_folder = proj_path + 'util_scripts/survey_files_2023/'
logs_folder = base_folder + 'logs/'

# SURVEY_TITLE = {
#     'en': 'Want to help us?',
#     'es': '¿Quieres ayudarnos?',
#     'ca': 'Ens vols donar un cop de mà?',
#     'nl': 'Wil je ons helpen?',
#     'el': 'Θέλετε να μας βοηθήσετε;',
#     'it': 'Vuoi aiutarci?'
# }

SURVEY_TEXT_DEFAULT = {
    "en": { "title":"Take our survey","message":"Share your perspective! Participate in our survey and help us improve." },
    "es": { "title":"Completa nuestra encuesta","message":"¡Comparte tu perspectiva! Participa en nuestra encuesta y ayúdanos a mejorar." },
    "ca": { "title":"Completa la nostra enquesta","message":"Comparteix la teva perspectiva! Participa en la nostra enquesta i ajuda'ns a millorar." },
    "el": { "title":"Συμπλήρωσε την έρευνά μας","message":"Μοιράσου την αποψή σου! Συμμετέχετε στην έρευνά μας και βοηθήστε μας να βελτιωθούμε." },
    "nl": { "title":"Doe mee aan onze enquête","message":"Deel je perspectief! Neem deel aan onze enquête en help ons verbeteren." },
    "it": { "title":"Compila il nostro sondaggio","message":"Condividi la tua prospettiva! Partecipa al nostro sondaggio e aiutaci a migliorare." }
}

SURVEY_TEXT = {
  "7": {
    "2": {
      "en": { "title":"Take our survey","message":"Share your perspective! Participate in our survey and help us improve." },
      "es": { "title":"Completa nuestra encuesta","message":"¡Comparte tu perspectiva! Participa en nuestra encuesta y ayúdanos a mejorar." },
      "ca": { "title":"Completa la nostra enquesta","message":"Comparteix la teva perspectiva! Participa en la nostra enquesta i ajuda'ns a millorar." },
      "el": { "title":"Συμπλήρωσε την έρευνά μας","message":"Μοιράσου την αποψή σου! Συμμετέχετε στην έρευνά μας και βοηθήστε μας να βελτιωθούμε." },
      "nl": { "title":"Doe mee aan onze enquête","message":"Deel je perspectief! Neem deel aan onze enquête en help ons verbeteren." },
      "it": { "title":"Compila il nostro sondaggio","message":"Condividi la tua prospettiva! Partecipa al nostro sondaggio e aiutaci a migliorare." }
    },
    "15": {
      "en": { "title":"We need your input","message":"Be a part of our research! Take the survey and contribute your insights." },
      "es": { "title":"Necesitamos tu opinión","message":"¡Forma parte de nuestra investigación! Completa la encuesta y aporta tus ideas." },
      "ca": { "title":"Necessitem la teva opinió","message": "Forma part de la nostra investigació! Completa l'enquesta i aporta les teves idees." },
      "el": { "title":"Χρειαζόμαστε την άποψή σας","message": "Γίνε μέρος της έρευνάς μας! Συμπλήρωσε το ερωτηματολόγιο και συνεισφέρετε τις απόψεις σας." },
      "nl": { "title":"We hebben jouw input nodig","message": "Maak deel uit van ons onderzoek! Vul de enquête in en draag jouw inzichten bij." },
      "it": { "title":"Abbiamo bisogno del tuo contributo","message": "Fai parte della nostra ricerca! Compila il sondaggio e contribuisci con le tue opinioni." }
    },
    "26": {
      "en": { "title":"Participate in our research","message":"Your voice matters! Help develop participation in science by participating in our survey." },
      "es": { "title":"Participa en nuestra investigación","message": "¡Tu voz es importante! Ayuda a fomentar la participación en la ciencia participando en nuestra encuesta." },
      "ca": { "title":"Participa en la nostra investigació","message": "La teva veu compta! Ajuda a desenvolupar la participació en la ciència participant en la nostra enquesta." },
      "el": { "title":"Συμμετέχετε στην έρευνά μας","message": "Η φωνή σου μετράει! Βοήθησε στην ανάπτυξη της συμμετοχής στην επιστήμη συμμετέχοντας στην έρευνά μας." },
      "nl": { "title":"Neem deel aan ons onderzoek","message": "Jouw stem telt! Draag bij aan de ontwikkeling van participatie in wetenschap door deel te nemen aan onze enquête." },
      "it": { "title":"Partecipa alla nostra ricerca","message": "La tua voce conta! Aiuta a sviluppare la partecipazione nella scienza partecipando al nostro sondaggio." }
    }
  },
  "8":{
    "8":{
      "en": { "title":"Share your Insights","message":"We want to hear from you! Participate in our survey and share your views." },
      "es": { "title":"Comparte tus ideas","message": "¡Queremos conocer tu opinión! Participa en nuestra encuesta y comparte tus puntos de vista." },
      "ca": { "title":"Comparteix les teves idees","message": "Volem sentir la teva opinió! Participa en la nostra enquesta i comparteix les teves perspectives." },
      "el": { "title":"Μοιραστείτε τις ιδέες σας","message": "Θέλουμε να ακούσουμε τη φωνή σου! Συμμετέχετε στην έρευνά μας και μοιραστείτε τις απόψεις σας." },
      "nl": { "title":"Deel je inzichten","message": "Wij willen graag jouw mening horen! Doe mee aan onze enquête en deel jouw visie." },
      "it": { "title":"Condividi le tue opinioni","message": "Vogliamo sentire la tua voce! Partecipa al nostro sondaggio e condividi le tue opinioni." }
    },
    "19":{
      "en": { "title":"Participate in our study","message":"Shape the future of science! Contribute to research, and help us improve by participating in our survey." },
      "es": { "title":"Participa en nuestro estudio","message": "¡Contribuye al futuro de la ciencia! Colabora en la investigación y ayúdanos a mejorar participando en nuestra encuesta." },
      "ca": { "title":"Participa en el nostre estudi","message": "Volem sentir la teva opinió! Participa en la nostra enquesta i comparteix les teves perspectives." },
      "el": { "title":"Συμμετάσχετε στη μελέτη μας","message": "Συμβάλλετε στο μέλλον της επιστήμης! Συμμετάσχετε στην έρευνα και βοηθήστε μας να βελτιωθούμε συμπληρώνοντας το ερωτηματολόγιό μας." },
      "nl": { "title":"Neem deel aan ons onderzoek","message": "Vorm de toekomst van de wetenschap! Draag bij aan onderzoek en help ons verbeteren door deel te nemen aan onze enquête." },
      "it": { "title":"Partecipa al nostro studio","message": "Contribuisci al futuro della scienza! Partecipa alla ricerca e aiutaci a migliorare compilando il nostro sondaggio." }
    },
    "31":{
      "en": { "title":"Take our survey","message":"Share your perspective! Participate in our survey and help us improve." },
      "es": { "title":"Completa nuestra encuesta","message":"¡Comparte tu perspectiva! Participa en nuestra encuesta y ayúdanos a mejorar." },
      "ca": { "title":"Completa la nostra enquesta","message":"Comparteix la teva perspectiva! Participa en la nostra enquesta i ajuda'ns a millorar." },
      "el": { "title":"Συμπλήρωσε την έρευνά μας","message":"Μοιράσου την αποψή σου! Συμμετέχετε στην έρευνά μας και βοηθήστε μας να βελτιωθούμε." },
      "nl": { "title":"Doe mee aan onze enquête","message":"Deel je perspectief! Neem deel aan onze enquête en help ons verbeteren." },
      "it": { "title":"Compila il nostro sondaggio","message":"Condividi la tua prospettiva! Partecipa al nostro sondaggio e aiutaci a migliorare." }
    }
  },
  "9":{
    "12":{
      "en": { "title":"We need your input","message":"Be a part of our research! Take the survey and contribute your insights." },
      "es": { "title":"Necesitamos tu opinión","message":"¡Forma parte de nuestra investigación! Completa la encuesta y aporta tus ideas." },
      "ca": { "title":"Necessitem la teva opinió","message": "Forma part de la nostra investigació! Completa l'enquesta i aporta les teves idees." },
      "el": { "title":"Χρειαζόμαστε την άποψή σας","message": "Γίνε μέρος της έρευνάς μας! Συμπλήρωσε το ερωτηματολόγιο και συνεισφέρετε τις απόψεις σας." },
      "nl": { "title":"We hebben jouw input nodig","message": "Maak deel uit van ons onderzoek! Vul de enquête in en draag jouw inzichten bij." },
      "it": { "title":"Abbiamo bisogno del tuo contributo","message": "Fai parte della nostra ricerca! Compila il sondaggio e contribuisci con le tue opinioni." }
    }
  }
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

    user_language = 'en'
    try:
        user = TigaUser.objects.get(pk=this_uuid)
        if len( user.user_reports.all() ) > 0:
            first_report = user.user_reports.all().order_by('-creation_time').first()
            os_language =  first_report.app_language
            if os_language in ['en', 'es', 'ca', 'nl', 'el', 'it']:
                user_language = os_language

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

        send_notification = SentNotification(sent_to_user=user, notification=notification)
        send_notification.save()

        # then push notification
        json_notif = custom_render_notification(sent_notification=send_notification, recipient=None, locale=user_language)
        generic_send(user.device_token, title_native, message_native)

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
    expert_comment = sent_notification.notification.notification_content.get_title_locale_safe(locale)
    expert_html = sent_notification.notification.notification_content.get_body_locale_safe(locale)

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

    send_notification = SentNotification(sent_to_topic=topic, notification=notification)
    send_notification.save()

    json_notif = custom_render_notification(sent_notification=send_notification, recipient=None, locale='en')
    push_result = generic_send_to_topic(topic_code=topic.topic_code, title=notification_content.title_en, message='', json_notif=json_notif)



if __name__ == '__main__':
    send_message_to_list(sys.argv[1:])
