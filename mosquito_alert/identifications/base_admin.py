from django.contrib import admin
from django.utils.translation import gettext_lazy as _


##########################
# Identifier profile admin
##########################
class BaseIdentifierProfileAdmin(admin.options.BaseModelAdmin):
    _identifier_profile_fields = ("is_identifier", "is_superidentifier")

    fields = None
    fieldsets = (
        (
            _("Identifier information"),
            {
                "fields": _identifier_profile_fields,
            },
        ),
    )

    list_display = _identifier_profile_fields
    list_filter = _identifier_profile_fields
