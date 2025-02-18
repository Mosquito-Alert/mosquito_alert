from typing import Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.template.exceptions import TemplateDoesNotExist
from django.utils.translation import activate, deactivate, gettext as _

from tigaserver_app.models import Notification, NotificationContent

from .models import IdentificationTask

User = get_user_model()


def create_notification_content_finished_validation(identification_task: IdentificationTask, commit: bool = True) -> NotificationContent:
    report_user = identification_task.report.user

    # Set the preferred language if it is supported, otherwise default to English
    user_language_code = 'en'
    if report_user.locale:
        user_language_code = report_user.locale if report_user.locale in dict(settings.LANGUAGES) else 'en'

    # Initialize contexts for English and user's preferred language
    context_en = {}
    context_native = {}

    # Add picture link if available
    picture_url = identification_task.photo.get_medium_url()
    if picture_url:
        context_en['picture_link'] = context_native['picture_link'] = picture_url

    context_en['expert_note'] = context_native['expert_note'] = identification_task.public_note

    # Include any specific message for the user
    if identification_task.message_for_user:
        context_en['message_for_user'] = context_native['message_for_user'] = identification_task.message_for_user

    # Add map link if report is published
    if identification_task.report.published:
        map_url = identification_task.report.public_map_url
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

    taxon_name = identification_task.taxon.name if identification_task.taxon else ''

    # Set the language to the user's preference
    activate(user_language_code)
    title_native = _("your_picture_has_been_validated_by_an_expert")
    # NOTE: confidence_label is translatable
    context_native['validation_category'] = "{} ({})".format(taxon_name, identification_task.confidence_label)

    # Get the message in English
    activate('en')
    title_en = _("your_picture_has_been_validated_by_an_expert")
    # NOTE: confidence_label is translatable
    context_en['validation_category'] = "{} ({})".format(taxon_name, identification_task.confidence_label)

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

def send_finished_identification_task_notification(identification_task: IdentificationTask, as_user: Optional[User] = None) -> None:
    notification = Notification.objects.create(
        report=identification_task.report,
        expert=as_user,
        notification_content=create_notification_content_finished_validation(identification_task=identification_task)
    )
    notification.send_to_user(user=identification_task.report.user)
