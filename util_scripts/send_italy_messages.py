import os, sys
import csv

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path + "util_scripts/")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

from tigaserver_app.models import NotificationContent, Notification, NotificationTopic
from django.contrib.auth.models import User

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

# cleanup
# delete from tigaserver_app_sentnotification where notification_id in ( select n.id from tigaserver_app_notification n, tigaserver_app_notificationcontent nc where nc.id = n.notification_content_id and nc.notification_label = 'notif_ita_06022023' );
# delete from tigaserver_app_acknowledgednotification where notification_id in ( select n.id from tigaserver_app_notification n, tigaserver_app_notificationcontent nc where nc.id = n.notification_content_id and nc.notification_label = 'notif_ita_06022023' );
# delete from tigaserver_app_notification where notification_content_id in ( select id from tigaserver_app_notificationcontent nc where nc.notification_label = 'notif_ita_06022023' );

def main(pk_notif_1, pk_notif_2):
    sender = User.objects.get(pk=38)  # mosquitoalert

    notification_content_1 = NotificationContent.objects.get(pk=pk_notif_1)
    for topic_code in send_to_1:
        notification_1 = Notification(expert=sender, notification_content=notification_content_1)
        notification_1.save()
        topic = NotificationTopic.objects.get(topic_code=topic_code)
        notification_1.send_to_topic(topic=topic)

    notification_content_2 = NotificationContent.objects.get(pk=pk_notif_2)
    for topic_code in send_to_2:
        notification_2 = Notification(expert=sender, notification_content=notification_content_2)
        notification_2.save()
        topic = NotificationTopic.objects.get(topic_code=topic_code)
        notification_2.send_to_topic(topic=topic)

if __name__ == '__main__':
    # args = sys.argv[1:]
    # main(pk_notif_1=1442611,pk_notif_2=1442612)
    # production
    main(pk_notif_1=1442835,pk_notif_2=1442836)