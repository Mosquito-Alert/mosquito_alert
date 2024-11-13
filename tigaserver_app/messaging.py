from django.conf import settings
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.template.exceptions import TemplateDoesNotExist
from django.utils.translation import activate, deactivate, gettext as _

User = get_user_model()

def send_new_award_notification(award: 'tigaserver_app.models.Award') -> None:
    from .models import Notification, NotificationContent   

    if settings.DISABLE_ACHIEVEMENT_NOTIFICATIONS:
        return

    user = award.given_to
    # Set the preferred language if it is supported, otherwise default to English
    user_language_code = 'en'
    if user.language_iso2:
        user_language_code = user.language_iso2 if user.language_iso2 in dict(settings.LANGUAGES) else 'en'

    # Initialize contexts for English and user's preferred language
    context_en = {}
    context_native = {}

    report = award.report
    if report:
        if report.package_version and report.package_version <= settings.MINIMUM_PACKAGE_VERSION_SCORING_NOTIFICATIONS:
            return

        # Add picture link if available
        picture_url = report.get_final_photo_url_for_notification()
        if not picture_url:
            pic = report.get_first_visible_photo()
            if pic:
                picture_url = pic.get_medium_url()

            if picture_url:
                context_en['picture_link'] = context_native['picture_link'] = picture_url

    # Add XP earning
    award_xp = award.special_award_xp if award.special_award_xp else (award.category.xp_points if award.category else 0)
    context_en['amount_awarded'] = context_native['amount_awarded'] = award_xp

    reason_awarded_txt = award.special_award_text if award.special_award_text else (award.category.category_label if award.category else 0)
    activate(user_language_code)
    # Add award text for native user's language
    context_native['reason_awarded'] = _(reason_awarded_txt)
    title_native = _("you_just_received_a_points_award")

    activate('en')
    # Add award text for english
    context_en['reason_awarded'] = _(reason_awarded_txt)
    title_en = _("you_just_received_a_points_award")

    deactivate()

    # Function for rendering HTML body based on language template
    def render_body_html(template_lang, context):
        try:
            result_template = render_to_string(f'tigaserver_app/award_notification_{template_lang}.html', context)
        except TemplateDoesNotExist:
            result_template = render_to_string('tigaserver_app/award_notification_en.html', context)

        return result_template.replace('&amp;', '&').encode('ascii', 'xmlcharrefreplace').decode('UTF-8')

    # Render HTML bodies
    body_html_en = render_body_html('en', context_en)
    body_html_native = render_body_html(user_language_code, context_native)

    notification_content = NotificationContent.objects.create(
        native_locale=user_language_code,
        title_en=title_en,
        title_native=title_native,
        body_html_en=body_html_en,
        body_html_native=body_html_native
    )

    notification = Notification.objects.create(
        report=report,
        expert=User.objects.get(pk=24),
        notification_content=notification_content
    )
    notification.send_to_user(user=user)
