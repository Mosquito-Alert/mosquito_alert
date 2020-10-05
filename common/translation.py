import html.entities
import tigaserver_project.settings as conf
from django.conf import settings
from django.utils.translation import ugettext
from django.utils import translation


def get_translation_in(string, locale):
    translation.activate(locale)
    val = ugettext(string)
    translation.deactivate()
    return val

def get_locale_for_en(report):
    if report is not None:
        if report.app_language is not None and report.app_language != '':
            if report.app_language != 'ca' and report.app_language != 'en' and report.app_language != 'es':
                report_locale = report.app_language
                for lang in settings.LANGUAGES:
                    if lang[0] == report_locale:
                        return report_locale
    return 'en'