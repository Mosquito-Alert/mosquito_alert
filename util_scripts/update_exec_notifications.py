'''
Re-render notification htmls
'''
import os, sys
import csv
from django.core.wsgi import get_wsgi_application

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

application = get_wsgi_application()

from tigaserver_app.models import Notification
from tigacrafting.models import ExpertReportAnnotation
from common.translation import get_locale_for_native, get_translation_in
from django.template.loader import TemplateDoesNotExist
from django.template.loader import render_to_string
from tigacrafting.views import get_sigte_report_link, get_sigte_map_info
import django


def get_report_annotation_from_report(report_uuid):
    for n in Notification.objects.filter(report=report_uuid):
        if n.expert.id == 25:
            try:
                report_annotation = ExpertReportAnnotation.objects.get(user_id=n.expert.id, report_id=report_uuid)
                return report_annotation
            except ExpertReportAnnotation.DoesNotExist:
                print("User {0} has no executive validation for report {1}".format( n.user.id, report_uuid ))
                return None
    return None


def get_notification_content_from_report(report_uuid):
    for n in Notification.objects.filter(report=report_uuid):
        if n.expert.id == 25 and "Your picture has been validated by an expert!" in n.notification_content.title_en:
            return n.notification_content
    return None


def update_notification_content(notificationcontent, report_annotation, current_domain):

    notification_content = notificationcontent
    context_en = {}
    context_native = {}
    locale_for_native = get_locale_for_native(report_annotation.report)

    notification_content.title_en = get_translation_in("your_picture_has_been_validated_by_an_expert", "en")
    notification_content.title_native = get_translation_in("your_picture_has_been_validated_by_an_expert", locale_for_native)
    notification_content.native_locale = locale_for_native

    if report_annotation.report.get_final_photo_url_for_notification():
        context_en['picture_link'] = 'http://' + current_domain + report_annotation.report.get_final_photo_url_for_notification()
        context_native['picture_link'] = 'http://' + current_domain + report_annotation.report.get_final_photo_url_for_notification()

    # if this report_annotation does not have comments, look for comments in
    # the other report annotations
    if report_annotation.edited_user_notes:
        clean_annotation = report_annotation.edited_user_notes
        context_en['expert_note'] = clean_annotation
        context_native['expert_note'] = clean_annotation
    else:
        if report_annotation.report.expert_report_annotations.filter(simplified_annotation=False).exists():
            non_simplified_annotation = report_annotation.report.expert_report_annotations.filter(simplified_annotation=False).first()
            if non_simplified_annotation.edited_user_notes:
                clean_annotation = non_simplified_annotation.edited_user_notes
                context_en['expert_note'] = clean_annotation
                context_native['expert_note'] = clean_annotation

    if report_annotation.message_for_user:
        clean_annotation = report_annotation.message_for_user
        context_en['message_for_user'] = clean_annotation
        context_native['message_for_user'] = clean_annotation

    if report_annotation.report:
        clean_annotation = django.utils.html.escape(report_annotation.report.get_final_combined_expert_category_public_map_euro('en'))
        clean_annotation = clean_annotation.encode('ascii', 'xmlcharrefreplace').decode('utf-8')
        context_en['validation_category'] = clean_annotation
        clean_annotation = django.utils.html.escape(report_annotation.report.get_final_combined_expert_category_public_map_euro(locale_for_native))
        clean_annotation = clean_annotation.encode('ascii', 'xmlcharrefreplace').decode('utf-8')
        context_native['validation_category'] = clean_annotation
        map_data = get_sigte_map_info(report_annotation.report)

        if map_data:
            context_en['map_link'] = get_sigte_report_link(report_annotation.report, "en", current_domain)
            context_native['map_link'] = get_sigte_report_link(report_annotation.report, locale_for_native, current_domain)

    notification_content.body_html_en = render_to_string('tigacrafting/validation_message_template_en.html', context_en).replace('&amp;', '&')

    try:
        notification_content.body_html_native = render_to_string('tigacrafting/validation_message_template_' + locale_for_native + '.html', context_native).replace('&amp;', '&')
    except TemplateDoesNotExist:
        notification_content.body_html_native = render_to_string('tigacrafting/validation_message_template_en.html', context_native).replace('&amp;', '&')

    notification_content.save()


def update_report(report_uuid):
    report_annotation = get_report_annotation_from_report(report_uuid)
    notification_content = get_notification_content_from_report(report_uuid)
    update_notification_content(notification_content, report_annotation, 'webserver.mosquitoalert.com')

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