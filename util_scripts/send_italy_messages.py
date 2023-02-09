import os, sys
import csv

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path + "util_scripts/")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

from tigaserver_app.models import NotificationContent, Notification, TigaUser, SentNotification, NotificationTopic
from django.contrib.auth.models import User
from tigacrafting.messaging import generic_send_to_topic

send_to_1 = [
    'ITC2', #Valle d'Aosta
    'ITC1', #Piemonte
    'ITC4', #Lombardia
    'ITH1', #Provincia Autonoma di Bolzano/Bozen
    'ITH2', #Provincia Autonoma di Trento
    'ITH3', #Veneto
    'ITH4', #Friuli-Venezia Giulia
    'ITC3', #Liguria
    'ITH5', #Emilia-Romagna
]

send_to_2 = [
    'ITI4', #Lazio
    'ITI3', #Marche
    'ITI1', #Toscana
    'ITI2', #Umbria
    'ITF1', #Abruzzo
    'ITF5', #Basilicata
    'ITF6', #Calabria
    'ITF3', #Campania
    'ITF2', #Molise
    'ITF4', #Puglia
    'ITG1', #Sicily
    'ITG2', #Sardinia
]


def main(pk_notif_1, pk_notif_2):
    sender = User.objects.get(pk=38)  # mosquitoalert

    notification_content_1 = NotificationContent.objects.get(pk=pk_notif_1)
    notification_1 = Notification(expert=sender, notification_content=notification_content_1)
    notification_1.save()

    for topic_code in send_to_1:
        topic = NotificationTopic.objects.get(topic_code=topic_code)
        send_notification_1 = SentNotification(sent_to_topic=topic, notification=notification_1)
        send_notification_1.save()
        json_notif_1 = {'id': send_notification_1.id}
        retval = generic_send_to_topic(topic_code=topic_code,title=notification_content_1.title_native,message="Segnalaci adesso una zanzara ! Nonostante l'inverno, a causa delle temperature miti alcune zanzare aliene continuino a circolare!", json_notif=json_notif_1)
        print(retval)

    notification_content_2 = NotificationContent.objects.get(pk=pk_notif_2)
    notification_2 = Notification(expert=sender, notification_content=notification_content_2)
    notification_2.save()

    for topic_code in send_to_2:
        topic = NotificationTopic.objects.get(topic_code=topic_code)
        send_notification_2 = SentNotification(sent_to_topic=topic, notification=notification_2)
        send_notification_2.save()
        json_notif_2 = {'id': send_notification_2.id}
        retval = generic_send_to_topic(topic_code=topic_code,title=notification_content_2.title_native,message="La stagione riproduttiva delle zanzare tigre va generalmente da maggio ad ottobre. Se ne vedi una segnalala! Potrebbe essere una segnalazione unica nel suo genere!", json_notif=json_notif_2)
        print(retval)


if __name__ == '__main__':
    # args = sys.argv[1:]
    # main(pk_notif_1=1442609,pk_notif_2=1442610)
    # production
    main(pk_notif_1=1442835,pk_notif_2=1442836)