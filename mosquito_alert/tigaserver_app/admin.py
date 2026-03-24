from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from django.utils.translation import gettext_lazy as _

from mosquito_alert.tigaserver_app.models import Report, ReportResponse,  Photo, OrganizationPin

from simple_history.admin import SimpleHistoryAdmin
from simple_history.utils import get_history_model_for_model


class ReportInline(admin.TabularInline):
    model = Report
    fields = ('version_UUID', 'report_id', 'user', 'version_number', 'creation_time', 'version_time', 'type', 'os')
    readonly_fields = ('version_UUID', 'report_id', 'user', 'version_number', 'creation_time', 'version_time', 'type', 'os')
    show_change_link = True
    extra = 0


class ReportResponseInline(admin.StackedInline):
    model = ReportResponse
    readonly_fields = ('question', 'answer')
    extra = 0
    max_num = 0


class PhotoInline(admin.StackedInline):
    model = Photo
    extra = 0
    max_num = 0
    readonly_fields = ('photo', 'report')


class ReportAdmin(SimpleHistoryAdmin):
    list_display = (
        'version_UUID', 'report_id', 'deleted', 'user', 'version_number', 'creation_time', 'version_time', 'type',
        'package_version', 'os',
    )
    list_filter = ['os', 'type', 'package_name', 'package_version']
    search_fields = ('version_UUID',)

    inlines = [ReportResponseInline, PhotoInline]

    readonly_fields = [
        "deleted",
        "deleted_at",
        "published",
        "report_id",
        "version_number",
        "type",
        "user",
        "session",
        "server_upload_time",
        "updated_at",
        "version_time",
        "phone_upload_time",
        "creation_time",
        "timezone"
    ]

    fieldsets = [
        (
            _('General info'),
            {
                "fields": [
                    ("report_id", "version_number"),
                    ("published",),
                    ("hide", "deleted", "deleted_at"),
                    "type",
                    "user",
                    ("session",),
                    ("server_upload_time", "updated_at"),
                    ("version_time", "datetime_fix_offset"),
                    ("creation_time", "phone_upload_time")
                ]
            }
        ),
        (
            _("Location information"),
            {
                "fields": [
                    ("country", "nuts_2", "nuts_3"),
                    "location_choice",
                    "point",
                    "timezone"
                ]
            }
        ),
        (
            _("Other"),
            {
                "fields": [
                    ("mobile_app",),
                    ("package_name", "package_version", "app_language"),
                    ("device",),
                    ("device_manufacturer", "device_model"),
                    ("os", "os_version", "os_language"),
                    "note",
                    "tags"
                ],
                "classes": ["collapse",]
            }
        )
    ]

    def get_readonly_fields(self, request, obj=None):
        # Only allow to edit 'hide' field.
        result = super().get_readonly_fields(request, obj)

        readonly_fields = [field.name for field in self.model._meta.get_fields()]
        allow_edit_fields = ['hide',]

        for field_name in readonly_fields:
            if not field_name in allow_edit_fields:
                result.append(field_name)

        return result

    def get_fieldsets(self, request, obj = None):
        result = super().get_fieldsets(request, obj)

        if not obj:
            return result

        extra_fieldsets = []
        if obj.type == Report.TYPE_ADULT:
            extra_fieldsets.append(
                (
                    _("Specific information"),
                    {
                        "fields": [
                            ("event_environment", "event_moment"),
                            "user_perceived_mosquito_specie",
                            ("user_perceived_mosquito_thorax", "user_perceived_mosquito_abdomen", "user_perceived_mosquito_legs")
                        ]
                    }
                )
            )
        elif obj.type == Report.TYPE_BITE:
            extra_fieldsets.append(
                (
                    _("Specific information"),
                    {
                        "fields": [
                            ("event_environment", "event_moment"),
                            "bite_count",
                            ("head_bite_count", "left_arm_bite_count", "right_arm_bite_count", "chest_bite_count", "left_leg_bite_count", "right_leg_bite_count")
                        ]
                    }
                )
            )
        elif obj.type == Report.TYPE_SITE:
            extra_fieldsets.append(
                (
                    _("Specific information"),
                    {
                        "fields": [
                            "breeding_site_type",
                            "breeding_site_has_water",
                            "breeding_site_in_public_area",
                            "breeding_site_has_near_mosquitoes",
                            "breeding_site_has_larvae"
                        ]
                    }
                )
            )

        return result + extra_fieldsets

    def render_history_view(self, request, template, context, **kwargs):
        user_model = get_history_model_for_model(Report)._meta.get_field('history_user').related_model
        context['admin_user_view'] = "admin:%s_%s_change" % (
            user_model._meta.app_label,
            user_model._meta.model_name
        )

        return super().render_history_view(
            request=request,
            template=template,
            context=context,
            **kwargs
        )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class OrganizationPinAdmin(GISModelAdmin):
    list_display = ('id', 'point', 'textual_description', 'page_url')
    list_filter = ['textual_description', 'page_url']
    search_fields = ['textual_description', 'page_url']


admin.site.register(Report, ReportAdmin)
admin.site.register(OrganizationPin, OrganizationPinAdmin)
