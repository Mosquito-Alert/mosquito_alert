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
    extra = 0


class PhotoAdmin(admin.ModelAdmin):
    list_display = ('id', 'photo', 'image_', 'report')


class PhotoInline(admin.StackedInline):
    model = Photo
    extra = 0


class ReportAdmin(admin.ModelAdmin):
    list_display = ('report_id', 'version_number', 'creation_time', 'version_time', 'type', 'mission',
                    'package_version', 'os')
    inlines = [ReportResponseInline, PhotoInline]
    ordering = ('creation_time', 'report_id', 'version_number')


class FixAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_coverage_uuid', 'fix_time', 'server_upload_time')
    ordering = ('fix_time',)


admin.site.register(TigaUser, UserAdmin)
admin.site.register(Report, ReportAdmin)
admin.site.register(Fix, FixAdmin)
admin.site.register(Configuration, ConfigurationAdmin)
admin.site.register(Mission, MissionAdmin)
admin.site.register(Photo, PhotoAdmin)
