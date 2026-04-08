from modeltranslation.translator import TranslationOptions, register

from .models import NotificationContent


@register(NotificationContent)
class NotificationContentTranslationOptions(TranslationOptions):
    fields = ("title", "body_html")
