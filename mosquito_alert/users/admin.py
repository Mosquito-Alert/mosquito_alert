from django.contrib import admin
from mosquito_alert.geo.models import NutsEurope

from mosquito_alert.reports.admin import ReportInline
from mosquito_alert.devices.admin import DeviceInline

from .models import UserStat, TigaUser


@admin.register(UserStat)
class UserStatAdmin(admin.ModelAdmin):
    search_fields = ("user__username",)
    ordering = ("user__username",)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "nuts2_assignation":
            kwargs["queryset"] = NutsEurope.objects.all().order_by(
                "europecountry__name_engl", "name_latn"
            )
        return super(UserStatAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs
        )


@admin.register(TigaUser)
class TigaUserAdmin(admin.ModelAdmin):
    list_display = ("user_UUID", "registration_time", "score_v2")
    fields = (
        "user_UUID",
        "registration_time",
        "locale",
        ("score_v2", "last_score_update"),
        ("last_location", "last_location_update"),
    )
    readonly_fields = (
        "user_UUID",
        "registration_time",
        "score_v2",
        "last_score_update",
        "last_location",
        "last_location_update",
    )
    search_fields = ("user_UUID",)
    ordering = ("registration_time",)
    inlines = [ReportInline, DeviceInline]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
