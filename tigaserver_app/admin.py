from django.contrib import admin
from tigaserver_app.models import Notification, TigaUser, Mission, MissionTrigger, MissionItem, Report, ReportResponse,  Photo, \
    Fix, Configuration, CoverageArea
from rest_framework.authtoken.models import Token
import csv
from django.utils.encoding import smart_str
from django.http.response import HttpResponse
from django.utils.html import mark_safe


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
    actions = [export_full_csv, export_full_csv_sc]

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
                    'package_version', 'os', 'n_photos', 'map_link', 'movelab_score', 'crowd_score')
    inlines = [ReportResponseInline, PhotoInline]
    ordering = ('creation_time', 'report_id', 'version_number')
    readonly_fields = ('deleted', 'version_UUID', 'user', 'report_id', 'version_number', 'other_versions_of_this_report', 'creation_time', 'version_time', 'server_upload_time', 'phone_upload_time', 'type', 'mission', 'location_choice', 'current_location_lon', 'current_location_lat', 'selected_location_lon', 'selected_location_lat', 'note', 'package_name', 'package_version', 'device_manufacturer', 'device_model', 'os', 'os_version', 'os_language', 'app_language', 'n_photos', 'lon', 'lat', 'tigaprob', 'tigaprob_text', 'site_type', 'site_type_trans', 'embornals', 'fonts', 'basins', 'buckets', 'wells', 'other', 'masked_lat', 'masked_lon', 'map_link', 'movelab_score', 'crowd_score')
    fields = ('hide', 'deleted', 'map_link', 'version_UUID', 'user', 'report_id', 'version_number', 'other_versions_of_this_report', 'creation_time', 'version_time', 'server_upload_time','phone_upload_time', 'type', 'mission', 'location_choice', 'current_location_lon', 'current_location_lat', 'selected_location_lon', 'selected_location_lat', 'note', 'package_name', 'package_version', 'device_manufacturer', 'device_model', 'os', 'os_version', 'os_language', 'app_language', 'n_photos', 'lon', 'lat', 'tigaprob', 'tigaprob_text', 'site_type', 'site_type_trans', 'embornals', 'fonts', 'basins', 'buckets', 'wells', 'other', 'masked_lat', 'masked_lon', 'movelab_score', 'crowd_score')
    list_filter = ['os', 'type', 'mission', 'package_name', 'package_version']
    actions = [export_full_csv, export_full_csv_sc]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def other_versions_of_this_report(self, obj):
        return obj.other_versions
    other_versions_of_this_report.allow_tags = True

    def movelab_score(self, obj):
        return obj.movelab_score

    def crowd_score(self, obj):
        return obj.crowd_score

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
        if not obj.report.deleted and not obj.report.hide and not obj.hide and obj.report.latest_version:
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
    readonly_fields = ('deleted', 'uuid', 'photo', 'small_image_', 'user', 'date', 'report_link', 'other_report_versions', 'map_link')
    fields = ('hide', 'deleted', 'uuid', 'date', 'user', 'photo', 'report_link', 'other_report_versions', 'map_link', 'small_image_')
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

    def other_report_versions(self, obj):
        return obj.report.other_versions
    other_report_versions.allow_tags = True

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
    list_display = ('report', 'user', 'expert', 'date_comment', 'expert_comment', 'expert_html', 'photo_url', 'acknowledged')
    search_fields = ['report__version_UUID','user__user_UUID']

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name=='report':
            kwargs["queryset"] = Report.objects.order_by("version_UUID")
        return super(NotificationAdmin,self).formfield_for_foreignkey(db_field,request,**kwargs)

admin.site.register(TigaUser, UserAdmin)
admin.site.register(Report, ReportAdmin)
admin.site.register(Fix, FixAdmin)
admin.site.register(Configuration, ConfigurationAdmin)
admin.site.register(Mission, MissionAdmin)
admin.site.register(Photo, PhotoAdmin)
admin.site.register(ReportResponse, ReportResponseAdmin)
admin.site.register(CoverageArea, CoverageAreaAdmin)
admin.site.register(Notification, NotificationAdmin)
