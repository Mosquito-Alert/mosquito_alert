from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from tigaserver_app.models import Notification, TigaUser, Mission, MissionTrigger, MissionItem, Report, ReportResponse,  Photo, \
    Fix, Configuration, CoverageArea, OWCampaigns, OrganizationPin, NotificationTopic, MobileApp, Device
import csv
from django.utils.encoding import smart_str
from django.http.response import HttpResponse
from django.utils.html import mark_safe
from django.utils.translation import ugettext_lazy as _

from simple_history.admin import SimpleHistoryAdmin
from simple_history.utils import get_history_model_for_model

def export_full_csv(modeladmin, request, queryset):
    response = HttpResponse(mimetype='text/csv')
    this_meta = queryset[0]._meta
    response['Content-Disposition'] = 'attachment; filename=tigatrapp_export_ ' + smart_str(this_meta.db_table) + '.csv'
    writer = csv.writer(response, csv.excel, quoting=csv.QUOTE_NONNUMERIC)
    response.write(u'\ufeff'.encode('utf8')) # BOM (optional...Excel needs it to open UTF-8 file properly)
    colnames = []
    for field in this_meta.fields:
        colnames.append(smart_str(field.name))
    writer.writerow(colnames)
    for obj in queryset:
        this_row = []
        for field in this_meta.fields:
            this_row.append(smart_str(getattr(obj, field.name)))
        writer.writerow(this_row)
    return response
export_full_csv.short_description = u"Export Full CSV"


def export_full_csv_sc(modeladmin, request, queryset):
    response = HttpResponse(mimetype='text/csv')
    this_meta = queryset[0]._meta
    response['Content-Disposition'] = 'attachment; filename=tigatrapp_export_ ' + smart_str(this_meta.db_table) + '.csv'
    writer = csv.writer(response, csv.excel, delimiter=";",  quoting=csv.QUOTE_NONNUMERIC)
    response.write(u'\ufeff'.encode('utf8')) # BOM (optional...Excel needs it to open UTF-8 file properly)
    colnames = []
    for field in this_meta.fields:
        colnames.append(smart_str(field.name))
    writer.writerow(colnames)
    for obj in queryset:
        this_row = []
        for field in this_meta.fields:
            this_row.append(smart_str(getattr(obj, field.name)))
        writer.writerow(this_row)
    return response
export_full_csv_sc.short_description = u"Export Full Semi-Colon Separated Values"


admin.site.disable_action('delete_selected')

class ReportInline(admin.TabularInline):
    model = Report
    fields = ('version_UUID', 'report_id', 'user', 'version_number', 'creation_time', 'version_time', 'type', 'os')
    readonly_fields = ('version_UUID', 'report_id', 'user', 'version_number', 'creation_time', 'version_time', 'type', 'os')
    show_change_link = True
    extra = 0

class MobileAppAdmin(admin.ModelAdmin):
    list_display = ('package_name', 'package_version', 'created_at')
    fields = (
        'package_name', 'package_version',
        ('created_at', 'updated_at')
    )
    readonly_fields = ('created_at', 'updated_at')

class DeviceInline(admin.StackedInline):
    model = Device
    fields = (
        ('device_id', 'is_logged_in', 'last_login'),
        ('registration_id', 'active'),
        'type',
        'mobile_app',
        ('manufacturer', 'model'),
        ('os_name', 'os_version'),
        'os_locale',
        ('date_created', 'updated_at'),
    )
    readonly_fields = (
        'date_created',
        'updated_at',
        'is_logged_in',
        'last_login'
    )
    extra = 0

class UserAdmin(admin.ModelAdmin):
    list_display = ('user_UUID', 'registration_time', 'score_v2')
    fields = ('user_UUID', 'registration_time', 'locale', ('score_v2', 'last_score_update'), ('last_location', 'last_location_update'))
    readonly_fields = ('user_UUID', 'registration_time', 'score_v2', 'last_score_update', 'last_location', 'last_location_update')
    search_fields = ('user_UUID',)
    ordering = ('registration_time',)
    actions = [export_full_csv, export_full_csv_sc]
    inlines = [ReportInline, DeviceInline]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ConfigurationAdmin(admin.ModelAdmin):
    list_display = ('id', 'creation_time', 'samples_per_day')
    readonly_fields = ('creation_time', )


class MissionItemInline(admin.StackedInline):
    model = MissionItem
    extra = 1


class MissionTriggerInline(admin.TabularInline):
    model = MissionTrigger
    extra = 1


class MissionAdmin(admin.ModelAdmin):
    list_display = ('title_catalan', 'platform', 'creation_time', 'expiration_time')
    inlines = [MissionItemInline, MissionTriggerInline]
    ordering = ('creation_time',)


class ReportResponseInline(admin.StackedInline):
    model = ReportResponse
    readonly_fields = ('question', 'answer')
    extra = 0
    max_num = 0


class PhotoInline(admin.StackedInline):
    model = Photo
    extra = 0
    max_num = 0
    readonly_fields = ('photo', 'small_image_', 'report')


class ReportAdmin(SimpleHistoryAdmin):
    list_display = (
        'version_UUID', 'report_id', 'deleted', 'user', 'version_number', 'creation_time', 'version_time', 'type', 'mission',
        'package_version', 'os', 'n_photos'
    )
    list_filter = ['os', 'type', 'mission', 'package_name', 'package_version']
    search_fields = ('version_UUID',)

    inlines = [ReportResponseInline, PhotoInline]
    actions = [export_full_csv, export_full_csv_sc]

    readonly_fields = [
        "deleted",
        "deleted_at",
        "report_id",
        "version_number",
        "type",
        "user",
        "mission",
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
                    ("hide", "deleted", "deleted_at"),
                    "type",
                    "user",
                    ("mission","session"),
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

def export_csv_photo(modeladmin, request, queryset):
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=tigatrapp_photos.csv'
    writer = csv.writer(response, csv.excel)
    response.write(u'\ufeff'.encode('utf8')) # BOM (optional...Excel needs it to open UTF-8 file properly)
    writer.writerow([
        smart_str(u"id"),
        smart_str(u"url"),
        smart_str(u"user"),
        smart_str(u"report"),
        smart_str(u"date"),
        smart_str(u"report_lat"),
        smart_str(u"report_lon"),
        smart_str(u"report_note"),
        smart_str(u"report_type"),
        smart_str(u"report_responses"),
    ])
    for obj in queryset:
        writer.writerow([
            smart_str(obj.id),
            smart_str("http://%s%s" % (request.get_host(), obj.photo.url)),
            smart_str(obj.user),
            smart_str(obj.report),
            smart_str(obj.date),
            smart_str(obj.report.lat),
            smart_str(obj.report.lon),
            smart_str(obj.report.note),
            smart_str(obj.report.type),
            smart_str(obj.report.response_string),

        ])
    return response
export_csv_photo.short_description = u"Export Full CSV"


def export_csv_photo_crowdcrafting(modeladmin, request, queryset):
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=tigatrapp_crowdcrafting_photos.csv'
    writer = csv.writer(response, csv.excel)
    response.write(u'\ufeff'.encode('utf8')) # BOM (optional...Excel needs it to open UTF-8 file properly)
    writer.writerow([
        smart_str(u"id"),
        smart_str(u"uuid"),
    ])
    for obj in queryset:
        if not obj.report.deleted and not obj.report.hide and not obj.hide:
            writer.writerow([
                smart_str(obj.id),
                smart_str(obj.uuid),
        ])
    return response
export_csv_photo_crowdcrafting.short_description = u"Export Crowdcrafting CSV"


def hide_photos(modeladmin, request, queryset):
    queryset.update(hide=True)


hide_photos.short_description = u"Hide selected photos"


def show_photos(modeladmin, request, queryset):
    queryset.update(hide=False)


show_photos.short_description = u"Unhide selected photos"


class PhotoAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'deleted', 'hide', 'small_image_', 'user', 'date', 'report_link', 'map_link')
    list_filter = ['hide', 'report__package_name', 'report__package_version']
    readonly_fields = ('deleted', 'uuid', 'photo', 'small_image_', 'user', 'date', 'report_link', 'map_link')
    fields = ('hide', 'deleted', 'uuid', 'date', 'user', 'photo', 'report_link', 'map_link', 'small_image_')
    actions = [export_csv_photo, export_csv_photo_crowdcrafting, hide_photos, show_photos]
    list_max_show_all = 6000
    list_per_page = 400

    def user(self, obj):
        return obj.user.user_UUID

    def small_image_(self, obj):
        return mark_safe(obj.small_image_())

    def report_link(self, obj):
        return mark_safe('<a href="/admin/tigaserver_app/report/%s" target="_blank">%s</a>' % (obj.report.version_UUID, obj.report.version_UUID))
    report_link.allow_tags = True

    def map_link(self, obj):
        return mark_safe('<a href="/single_report_map/%s/" target="_blank">Show map</a>' % obj.report.version_UUID)
    map_link.allow_tags = True

    def deleted(self, obj):
        return obj.report.deleted

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class FixAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_coverage_uuid', 'fix_time', 'server_upload_time')
    ordering = ('fix_time',)
    readonly_fields = ('id', 'user_coverage_uuid', 'fix_time', 'server_upload_time', 'phone_upload_time', 'masked_lon', 'masked_lat', 'power')
    fields = ('id', 'user_coverage_uuid', 'fix_time', 'server_upload_time', 'phone_upload_time', 'masked_lon', 'masked_lat', 'power')
    actions = [export_full_csv, export_full_csv_sc]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ReportResponseAdmin(admin.ModelAdmin):
    list_display = ('report', 'question', 'answer')
    fields = ('report', 'question', 'answer')
    actions = [export_full_csv, export_full_csv_sc]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class CoverageAreaAdmin(admin.ModelAdmin):
    list_display = ('lat', 'lon', 'n_fixes', 'last_modified', 'latest_report_server_upload_time', 'latest_fix_id')
    fields = ('lat', 'lon', 'n_fixes', 'last_modified', 'latest_report_server_upload_time', 'latest_fix_id')

    def has_add_permission(self, request):
        return False


class NotificationAdmin(admin.ModelAdmin):
    #list_display = ('report', 'user', 'expert', 'date_comment', 'expert_comment', 'expert_html', 'photo_url', 'acknowledged')
    list_display = ('report', 'expert', 'date_comment', 'expert_comment', 'expert_html', 'photo_url')
    search_fields = ['report__version_UUID','user__user_UUID']

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name=='report':
            kwargs["queryset"] = Report.objects.order_by("version_UUID")
        return super(NotificationAdmin,self).formfield_for_foreignkey(db_field,request,**kwargs)


class OWCampaignsAdmin(admin.ModelAdmin):
    list_display = ('id', 'country', 'posting_address', 'campaign_start_date', 'campaign_end_date')
    list_filter = ['country__name_engl', 'posting_address']
    ordering = ['country', 'campaign_start_date', 'campaign_end_date']

class NotificationTopicAdmin(admin.ModelAdmin):
    list_display = ('id', 'topic_code', 'topic_description', 'topic_group')
    list_filter = ['topic_code', 'topic_description']
    ordering = ['id', 'topic_code', 'topic_description']


class OrganizationPinAdmin(OSMGeoAdmin):
    list_display = ('id', 'point', 'textual_description', 'page_url')
    list_filter = ['textual_description', 'page_url']
    search_fields = ['textual_description', 'page_url']


admin.site.register(TigaUser, UserAdmin)
admin.site.register(MobileApp, MobileAppAdmin)
admin.site.register(Report, ReportAdmin)
admin.site.register(Fix, FixAdmin)
admin.site.register(Configuration, ConfigurationAdmin)
admin.site.register(Mission, MissionAdmin)
admin.site.register(Photo, PhotoAdmin)
admin.site.register(ReportResponse, ReportResponseAdmin)
admin.site.register(CoverageArea, CoverageAreaAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(OWCampaigns, OWCampaignsAdmin)
admin.site.register(OrganizationPin, OrganizationPinAdmin)
admin.site.register(NotificationTopic, NotificationTopicAdmin)
