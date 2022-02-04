from django import template
from django.template.defaultfilters import stringfilter
from django.utils.translation import gettext as _

register = template.Library()

@register.filter
def translate_class_value(value):
    classes = {
        '1': _("Novice"),
        '2': _("Contributor"),
        '3': _("Expert"),
        '4': _("Master"),
        '5': _("Grandmaster")
    }
    return classes[value]