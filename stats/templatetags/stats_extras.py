from django import template
from django.utils.translation import gettext as _
import datetime

register = template.Library()


@register.filter
def translate_class_value(value):
    key = str(value)
    classes = {
        '1': _("Novice"),
        '2': _("Contributor"),
        '3': _("Expert"),
        '4': _("Master"),
        '5': _("Grandmaster")
    }
    return classes[key]


@register.filter
def translate_generic_string(value):
    return _(value)


def diff_month( date_now, date_before ):
    return (( date_now.year - date_before.year ) * 12 ) + (date_now.month - date_before.month)


@register.filter
def get_elapsed_label( date_before_str ):
    date_before = datetime.datetime.strptime(date_before_str, "%d/%m/%Y")
    now = datetime.datetime.now()
    diff = now - date_before
    if diff.days >= 30:
        diff_months = diff_month( now, date_before )
        if diff_months > 12:
            return str( int(diff_months / 12) ) + _(" years ago")
        else:
            return str( diff_months ) + _(" months ago")
    else:
        return str(diff.days) + _(" days ago")