from django.contrib import admin
from tigaserver_app.models import TigaUser, Mission, MissionTrigger, MissionItem, Report, ReportResponse,  Photo, \
    Fix, Configuration
from rest_framework.authtoken.models import Token
import csv
from django.utils.encoding import smart_str
from django.http.response import HttpResponse


def export_full_csv(modeladmin, request, queryset):
    response = HttpResponse(mimetype='text/csv')
    this_meta = queryset[0]._meta
    response['Content-Disposition'] = 'attachment; filename=tigatrapp_export_ ' + smart_str(this_meta.db_table) + '.csv'
    writer = csv.writer(response, csv.excel)
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


class MyTokenAdmin(admin.ModelAdmin):
    list_display = ('key', 'user', 'created')
    fields = ('user', 'key')
    ordering = ('-created',)


admin.site.unregister(Token)
admin.site.register(Token, MyTokenAdmin)

admin.site.disable_action('delete_selected')


class UserAdmin(admin.ModelAdmin):
    list_display = ('user_UUID', 'registration_time', 'number_of_reports_uploaded', 'ios_user')
    readonly_fields = ('user_UUID', 'registration_time', 'number_of_reports_uploaded', 'ios_user')
    actions = [export_full_csv]

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


class ReportAdmin(admin.ModelAdmin):
    list_display = ('report_id', 'deleted', 'user', 'version_number', 'creation_time', 'version_time', 'type', 'mission',
                    'package_version', 'os', 'n_photos', 'map_link')
    inlines = [ReportResponseInline, PhotoInline]
    ordering = ('creation_time', 'report_id', 'version_number')
    readonly_fields = ('deleted', 'version_UUID', 'user', 'report_id', 'version_number', 'other_versions_of_this_report', 'creation_time', 'version_time', 'server_upload_time', 'phone_upload_time', 'type', 'mission', 'location_choice', 'current_location_lon', 'current_location_lat', 'selected_location_lon', 'selected_location_lat', 'note', 'package_name', 'package_version', 'device_manufacturer', 'device_model', 'os', 'os_version', 'os_language', 'app_language', 'n_photos', 'lon', 'lat', 'tigaprob', 'tigaprob_text', 'site_type', 'site_type_trans', 'embornals', 'fonts', 'basins', 'buckets', 'wells', 'other', 'masked_lat', 'masked_lon', 'map_link')
    fields = ('hide', 'deleted', 'map_link', 'version_UUID', 'user', 'report_id', 'version_number', 'other_versions_of_this_report', 'creation_time', 'version_time', 'server_upload_time','phone_upload_time', 'type', 'mission', 'location_choice', 'current_location_lon', 'current_location_lat', 'selected_location_lon', 'selected_location_lat', 'note', 'package_name', 'package_version', 'device_manufacturer', 'device_model', 'os', 'os_version', 'os_language', 'app_language', 'n_photos', 'lon', 'lat', 'tigaprob', 'tigaprob_text', 'site_type', 'site_type_trans', 'embornals', 'fonts', 'basins', 'buckets', 'wells', 'other', 'masked_lat', 'masked_lon')
    list_filter = ['os', 'type', 'mission', 'package_name', 'package_version']
    actions = [export_full_csv]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def other_versions_of_this_report(self, obj):
        return obj.other_versions
    other_versions_of_this_report.allow_tags = True

    def map_link(self, obj):
        return '<a href="/single_report_map/%s/">Show map</a>' % obj.version_UUID
    map_link.allow_tags = True


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
        if not obj.report.deleted and not obj.hide:
            writer.writerow([
                smart_str(obj.id),
                smart_str(obj.uuid),
        ])
    return response
export_csv_photo_crowdcrafting.short_description = u"Export Crowdcrafting CSV"


class PhotoAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'deleted', 'hide', 'small_image_', 'user', 'date', 'report_link', 'map_link')
    list_filter = ['hide', 'report__package_name', 'report__package_version']
    readonly_fields = ('deleted', 'uuid', 'photo', 'small_image_', 'user', 'date', 'report_link', 'other_report_versions', 'map_link')
    fields = ('hide', 'deleted', 'uuid', 'date', 'user', 'photo', 'report_link', 'other_report_versions', 'map_link', 'small_image_')
    actions = [export_csv_photo, export_csv_photo_crowdcrafting]
    list_max_show_all = 2000

    def report_link(self, obj):
        return '<a href="/admin/tigaserver_app/report/%s">%s</a>' % (obj.report, obj.report)
    report_link.allow_tags = True

    def other_report_versions(self, obj):
        return obj.report.other_versions
    other_report_versions.allow_tags = True

    def map_link(self, obj):
        return '<a href="/single_report_map/%s/">Show map</a>' % obj.report
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
    actions = [export_full_csv]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ReportResponseAdmin(admin.ModelAdmin):
    list_display = ('report', 'question', 'answer')
    fields = ('report', 'question', 'answer')
    actions = [export_full_csv]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(TigaUser, UserAdmin)
admin.site.register(Report, ReportAdmin)
admin.site.register(Fix, FixAdmin)
admin.site.register(Configuration, ConfigurationAdmin)
admin.site.register(Mission, MissionAdmin)
admin.site.register(Photo, PhotoAdmin)
admin.site.register(ReportResponse, ReportResponseAdmin)
