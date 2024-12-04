from django.conf import settings
from django.template.loader import render_to_string
from django.template.exceptions import TemplateDoesNotExist
from django.utils.html import escape
from django.utils.translation import activate, deactivate, gettext as _

from tigaserver_app.models import Notification, NotificationContent

from .models import ExpertReportAnnotation

def create_notification_content_finished_validation(report_annotation: ExpertReportAnnotation, commit: bool = True) -> NotificationContent:
    report_user = report_annotation.report.user

    # Set the preferred language if it is supported, otherwise default to English
    user_language_code = 'en'
    if report_user.locale:
        user_language_code = report_user.locale if report_user.locale in dict(settings.LANGUAGES) else 'en'

    # Initialize contexts for English and user's preferred language
    context_en = {}
    context_native = {}

    # Add picture link if available
    picture_url = report_annotation.report.get_final_photo_url_for_notification()
    if picture_url:
        context_en['picture_link'] = context_native['picture_link'] = picture_url

    # Include expert note, either from current annotation or a related one
    expert_note = report_annotation.edited_user_notes or ExpertReportAnnotation.objects.filter(
        report=report_annotation.report,
        simplified_annotation=False,
        edited_user_notes__isnull=False
    ).exclude(
        pk=report_annotation.pk,
        edited_user_notes=""
    ).values_list('edited_user_notes', flat=True).first()
    if expert_note:
        context_en['expert_note'] = context_native['expert_note'] = expert_note

    # Include any specific message for the user
    if report_annotation.message_for_user:
        context_en['message_for_user'] = context_native['message_for_user'] = report_annotation.message_for_user

    # Validation category handling with language-specific sanitization
    def get_sanitized_validation_category(language_code):
        category = report_annotation.report.get_final_combined_expert_category_public_map_euro(language_code)
        return escape(category).encode('ascii', 'xmlcharrefreplace').decode('utf-8')

    context_en['validation_category'] = get_sanitized_validation_category('en')
    context_native['validation_category'] = get_sanitized_validation_category(user_language_code)

    # Add map link if report is published
    if report_annotation.report.published:
        map_url = report_annotation.report.public_map_url
        context_en['map_link'] = context_native['map_link'] = map_url

    # Function for rendering HTML body based on language template
    def render_body_html(template_lang, context):
        try:
            return render_to_string(f'tigacrafting/validation_message_template_{template_lang}.html', context).replace('&amp;', '&')
        except TemplateDoesNotExist:
            return render_to_string('tigacrafting/validation_message_template_en.html', context).replace('&amp;', '&')

    # Render HTML bodies
    body_html_en = render_body_html('en', context_en)
    body_html_native = render_body_html(user_language_code, context_native)

    # Set the language to the user's preference
    activate(user_language_code)
    title_native = _("your_picture_has_been_validated_by_an_expert")

    # Get the message in English
    activate('en')
    title_en = _("your_picture_has_been_validated_by_an_expert")

    deactivate()

    notification_content = NotificationContent(
        native_locale=user_language_code,
        title_en=title_en,
        title_native=title_native,
        body_html_en=body_html_en,
        body_html_native=body_html_native
    )
    if commit:
        notification_content.save()

    return notification_content

def send_finished_validation_notification(report_annotation: ExpertReportAnnotation) -> None:
    notification = Notification.objects.create(
        report=report_annotation.report,
        expert=report_annotation.user,
        notification_content=create_notification_content_finished_validation(report_annotation=report_annotation)
    )
    notification.send_to_user(user=report_annotation.report.user)
