from django.contrib import admin
from tigaserver_app.models import TigaUser, Mission, MissionTrigger, MissionItem, Report, ReportResponse,  Photo, \
    Fix, Configuration
from rest_framework.authtoken.models import Token


class MyTokenAdmin(admin.ModelAdmin):
    list_display = ('key', 'user', 'created')
    fields = ('user', 'key')
    ordering = ('-created',)


admin.site.unregister(Token)
admin.site.register(Token, MyTokenAdmin)


class UserAdmin(admin.ModelAdmin):
    list_display = ('user_UUID', 'registration_time', 'number_of_reports_uploaded')
    readonly_fields = ('user_UUID', 'registration_time', 'number_of_reports_uploaded')


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
    readonly_fields = ('photo', 'image_', 'report')


class ReportAdmin(admin.ModelAdmin):
    list_display = ('report_id', 'version_number', 'creation_time', 'version_time', 'type', 'mission',
                    'package_version', 'os', 'n_photos')
    inlines = [ReportResponseInline, PhotoInline]
    ordering = ('creation_time', 'report_id', 'version_number')
    readonly_fields = ('version_UUID', 'user', 'report_id', 'version_number', 'creation_time', 'version_time', 'server_upload_time', 'phone_upload_time', 'type', 'mission', 'location_choice', 'current_location_lon', 'current_location_lat', 'selected_location_lon', 'selected_location_lat', 'note', 'package_name', 'package_version', 'device_manufacturer', 'device_model', 'os', 'os_version', 'os_language', 'app_language', 'n_photos', 'lon', 'lat', 'tigaprob', 'tigaprob_text', 'site_type', 'site_type_trans', 'embornals', 'fonts', 'basins', 'buckets', 'wells', 'other', 'masked_lat', 'masked_lon')
    fields = ('version_UUID', 'user', 'report_id', 'version_number', 'creation_time', 'version_time', 'server_upload_time','phone_upload_time', 'type', 'mission', 'location_choice', 'current_location_lon', 'current_location_lat', 'selected_location_lon', 'selected_location_lat', 'note', 'package_name', 'package_version', 'device_manufacturer', 'device_model', 'os', 'os_version', 'os_language', 'app_language', 'n_photos', 'lon', 'lat', 'tigaprob', 'tigaprob_text', 'site_type', 'site_type_trans', 'embornals', 'fonts', 'basins', 'buckets', 'wells', 'other', 'masked_lat', 'masked_lon')


class PhotoAdmin(admin.ModelAdmin):
    list_display = ('id', 'photo', 'image_', 'report')
    readonly_fields = ('photo', 'image_', 'report')
    fields = ('photo', 'image_', 'report')


class FixAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_coverage_uuid', 'fix_time', 'server_upload_time')
    ordering = ('fix_time',)
    readonly_fields = ('id', 'user_coverage_uuid', 'fix_time', 'server_upload_time', 'phone_upload_time', 'masked_lon', 'masked_lat', 'power')
    fields = ('id', 'user_coverage_uuid', 'fix_time', 'server_upload_time', 'phone_upload_time', 'masked_lon', 'masked_lat', 'power')


admin.site.register(TigaUser, UserAdmin)
admin.site.register(Report, ReportAdmin)
admin.site.register(Fix, FixAdmin)
admin.site.register(Configuration, ConfigurationAdmin)
admin.site.register(Mission, MissionAdmin)
admin.site.register(Photo, PhotoAdmin)
