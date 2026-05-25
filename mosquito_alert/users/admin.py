from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import User

from mosquito_alert.geo.models import NutsEurope
from mosquito_alert.reports.admin import ReportInline
from mosquito_alert.devices.admin import DeviceInline

from .models import UserStat, TigaUser


class UserStatAdminInline(admin.StackedInline):
    model = UserStat
    can_delete = False

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "nuts2_assignation":
            kwargs["queryset"] = NutsEurope.objects.all().order_by(
                "europecountry__name_engl", "name_latn"
            )
        return super(UserStatAdminInline, self).formfield_for_foreignkey(
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


# Unregister default User admin
admin.site.unregister(User)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    inlines = [UserStatAdminInline]
