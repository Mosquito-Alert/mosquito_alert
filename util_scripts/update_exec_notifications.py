'''
Re-render notification htmls
'''
import os, sys
from django.core.wsgi import get_wsgi_application
from typing import Optional

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

application = get_wsgi_application()

from tigaserver_app.models import Notification, NotificationContent
from tigacrafting.models import ExpertReportAnnotation
from tigacrafting.messaging import create_notification_content_finished_validation


def get_report_annotation_from_report(report_uuid: str) -> Optional[ExpertReportAnnotation]:
    user_id = 25
    try:
        return ExpertReportAnnotation.objects.get(user_id=user_id, report_id=report_uuid)
    except ExpertReportAnnotation.DoesNotExist:
        print("User {0} has no executive validation for report {1}".format(user_id, report_uuid ))
        return None

def get_notification_content_from_report(report_uuid: str) -> Optional[NotificationContent]:
    return NotificationContent.objects.filter(
        title_en="Your picture has been validated by an expert!",
        notification_content__expert_id=25,
        notification_content__report_id=report_uuid,
    ).first()


def update_notification_content(notification_content_pk: int, report_annotation: ExpertReportAnnotation):
    notification_content = create_notification_content_finished_validation(
        report_annotation=report_annotation
    )
    notification_content.pk = notification_content_pk
    notification_content.save()


def update_report(report_uuid):
    report_annotation = get_report_annotation_from_report(report_uuid)
    notification_content = get_notification_content_from_report(report_uuid)
    update_notification_content(notification_content.pk, report_annotation)

def main():
    #update_report('9db5c877-c838-4f15-a188-8a33f0d4e3f6')
    #update_report('48b38189-7a60-4b3c-90ba-d1c52526b18a')
    count = ExpertReportAnnotation.objects.filter(validation_complete_executive=True).filter(user_id=94).count()
    i = 1
    for r in ExpertReportAnnotation.objects.filter(validation_complete_executive=True).filter(user_id=94).values('report_id'):
        update_report( r['report_id'] )
        print("Done {0} of {1}, uuid {2}".format( str(i), str(count), r['report_id']))
        i = i + 1


if __name__ == '__main__':
    main()