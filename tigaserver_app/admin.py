from django.contrib import admin
from tigaserver_app.models import TigaUser, Mission, MissionTrigger, MissionItem, Report, ReportResponse,  Photo, \
    Fix, Configuration


class UserAdmin(admin.ModelAdmin):
    list_display = ('user_UUID', 'registration_time', 'number_of_fixes_uploaded', 'number_of_reports_uploaded')


class ConfigurationAdmin(admin.ModelAdmin):
    list_display = ('id', 'creation_time', 'samples_per_day')
    readonly_fields = ('creation_time', )


class MissionItemInline(admin.TabularInline):
    model = MissionItem
    extra = 1


class MissionTriggerInline(admin.TabularInline):
    model = MissionTrigger
    extra = 1


class MissionAdmin(admin.ModelAdmin):
    inlines = [MissionItemInline, MissionTriggerInline]


class ReportResponseInline(admin.StackedInline):
    model = ReportResponse
    extra = 0


class PhotoAdmin(admin.ModelAdmin):
    list_display = ('id', 'photo', 'report')


class PhotoInline(admin.StackedInline):
    model = Photo
    extra = 0


class ReportAdmin(admin.ModelAdmin):
    list_display = ('version_UUID', 'user', 'report_id', 'version_number', 'version_time', 'type', 'mission')
    inlines = [ReportResponseInline, PhotoInline]


class FixAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'fix_time', 'server_upload_time')


admin.site.register(TigaUser, UserAdmin)
admin.site.register(Report, ReportAdmin)
admin.site.register(Fix, FixAdmin)
admin.site.register(Configuration, ConfigurationAdmin)
admin.site.register(Mission, MissionAdmin)
