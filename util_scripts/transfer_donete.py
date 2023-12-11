import os, sys
import time
import csv

# **** Before running this, make sure the parameter DISABLE_MAYBE_GIVE_AWARDS = True in the settings ****
# this avoids creating awards automatically when saving a report

proj_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

from tigaserver_app.models import (TigaUser, Report, ReportResponse, Photo, Award, UserSubscription, SentNotification,
                                   Notification, NotificationContent, AcknowledgedNotification)
from django.db import transaction

def main():
    start = time.time()

    production_user_ids = TigaUser.objects.values_list('pk', flat=True)
    donete_user_ids = TigaUser.objects.using("donete").values_list('pk', flat=True)
    temp_notification = Notification.objects.using("donete").get(pk=1)

    production_user_ids_set = set(production_user_ids)
    donete_user_ids_set = set(donete_user_ids)

    users_not_in_production = donete_user_ids_set - production_user_ids_set

    n_users = len(users_not_in_production)
    print("Processing {0} users".format( n_users ))
    user_n = 1

    # this is for testing, good user some reports with photos, etc
    with transaction.atomic():
        users_not_in_production = ['5dac0358-3a5d-485c-80e9-bc3c8264c506']
        for donete_user_uuid in users_not_in_production:
        #for donete_user_uuid in [single_user]:
            #
            # #1 Save user
            #
            print("\tGetting user {0} from donete".format(donete_user_uuid))
            donete_user = TigaUser.objects.using("donete").get(pk=donete_user_uuid)
            original_registration_date_donete = donete_user.registration_time
            print("\tSaving user {0} to production database".format(donete_user_uuid))
            donete_user.save(using="default")

            print("\tUser saved to production, adjusting registration time")
            donete_user.registration_time = original_registration_date_donete
            donete_user.save(update_fields=['registration_time'])

            #
            # #2 Save user reports
            #
            print("\tGetting reports for user {0} from donete".format(donete_user_uuid))
            donete_reports = Report.objects.using("donete").filter(user__user_UUID=donete_user_uuid)
            for donete_report in donete_reports:
                original_server_upload_time = donete_report.server_upload_time
                donete_report.save(using="default")
                print("\t\tSaved report {0} to production, adjusting server_upload_time".format(donete_report.version_UUID))
                donete_report.server_upload_time = original_server_upload_time
                donete_report.save(update_fields=['server_upload_time'])

                #
                # 3 save report responses for report
                #
                print("\t\tGetting report responses for user {0} from donete".format(donete_user_uuid))
                report_responses_donete = ReportResponse.objects.using("donete").filter(report__version_UUID=donete_report.version_UUID)
                for report_response in report_responses_donete:
                    report_response.id = None
                    report_response.save(using="default")
                    print("\t\t\tSaved report response {0} to production".format(report_response.id))

                #
                # 4 save photos for report
                #
                print("\t\tGetting photos for user {0} from donete".format(donete_user_uuid))
                photos_donete = Photo.objects.using("donete").filter(report__version_UUID=donete_report.version_UUID)
                for photo in photos_donete:
                    photo.id = None
                    photo.save(using="default")
                    print("\t\t\tSaved photo {0} to production".format(photo.id))

                #
                # 5 save awards for report
                #
                print("\t\tGetting awards for user {0} from donete".format(donete_user_uuid))
                awards_donete = Award.objects.using("donete").filter(report__version_UUID=donete_report.version_UUID)
                for award in awards_donete:
                    award.id = None
                    award.save(using="default")
                    print("\t\t\tSaved award {0} to production".format(award.id))

            #
            # 6 save user subscriptions for user
            #
            print("\t\tGetting user subscriptions for user {0} from donete".format(donete_user_uuid))
            subscriptions_donete = UserSubscription.objects.using("donete").filter(user__user_UUID=donete_user_uuid)
            for subscription in subscriptions_donete:
                subscription.id = None
                subscription.save(using="default")
                print("\t\t\tSaved subscription {0} to production".format(subscription.id))

            #
            # 7 save notification content for user notifications
            #
            print("\t\tGetting notification content for user {0} from donete".format(donete_user_uuid))
            sent_notifications_in_donete = SentNotification.objects.using("donete").filter(sent_to_user__user_UUID=donete_user_uuid)
            notifications_in_donete = Notification.objects.using("donete").filter(id__in=sent_notifications_in_donete.values('notification').distinct())
            notification_content_in_donete = NotificationContent.objects.using("donete").filter( id__in=notifications_in_donete.values('notification_content').distinct() )
            notification_content_table = {}
            for notification_content_donete in notification_content_in_donete:
                notification_content_donete_id = notification_content_donete.id
                notification_content_donete.id = None
                notification_content_donete.save(using="default")
                notification_content_table[notification_content_donete_id] = notification_content_donete.id
                print("\t\t\tSaved notification content with new id {0} to production, old id {1}".format(notification_content_donete.id, notification_content_donete_id))

            #
            # 8 save notifications
            #
            notification_table = {}
            for notification_donete in notifications_in_donete:
                notification_donete_id = notification_donete.id
                notification_content_donete_id = notification_donete.notification_content.id
                notification_donete.id = None
                notification_donete.notification_content = None
                notification_donete.save(using="default")
                notification_donete.notification_content = NotificationContent.objects.get(pk=notification_content_table[notification_content_donete_id])
                notification_donete.save(update_fields=['notification_content'])
                notification_table[notification_donete_id] = notification_donete.id
                print("\t\t\tSaved notification with new id {0} to production, old id {1}".format(notification_donete.id, notification_donete_id))

            #
            # 9 save sent notifications
            #
            for sent_notification_donete in sent_notifications_in_donete:
                sent_notification_donete_id = sent_notification_donete.id
                sent_notification_donete.id = None
                sent_notification_donete.notification = temp_notification
                sent_notification_donete.save(using="default")
                sent_notification_donete.notification = Notification.objects.get(pk=notification_table[sent_notification_donete_id])
                notification_donete.save(update_fields=['notification'])
                print("\t\t\tSaved sent notification with new id {0} to production".format(sent_notification_donete.id))

            #
            # 10 acknowledged notification
            #
            acknowledged_notifications_donete = AcknowledgedNotification.objects.using("donete").filter(user__user_UUID=donete_user_uuid)
            for acknowledged_notification_donete in acknowledged_notifications_donete:
                acknowledged_notification_donete.id = None
                acknowledged_notification_donete_notification_id = acknowledged_notification_donete.notification.id
                acknowledged_notification_donete.notification = temp_notification
                acknowledged_notification_donete.save(using="default")
                acknowledged_notification_donete.notification = Notification.objects.get(pk=notification_table[acknowledged_notification_donete_notification_id])
                acknowledged_notification_donete.save(update_fields=['notification'])
                print("\t\t\tSaved acknowledged notification with new id {0} to production".format(acknowledged_notification_donete.id))

            print("\tDone user {0} of {1}".format( user_n, n_users ))
            user_n += 1

            print("")

            end = time.time()
            elapsed = end - start
            print("Elapsed time {0}".format( str(elapsed) ))



if __name__ == '__main__':
    main()