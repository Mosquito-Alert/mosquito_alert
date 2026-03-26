from django.contrib import admin

from .models import Device, MobileApp


@admin.register(MobileApp)
class MobileAppAdmin(admin.ModelAdmin):
    list_display = ("package_name", "package_version", "created_at")
    fields = ("package_name", "package_version", ("created_at", "updated_at"))
    readonly_fields = ("created_at", "updated_at")


class DeviceInline(admin.StackedInline):
    model = Device
    fields = (
        ("device_id", "active_session", "last_login"),
        ("registration_id", "active"),
        "type",
        "mobile_app",
        ("manufacturer", "model"),
        ("os_name", "os_version"),
        "os_locale",
        ("date_created", "updated_at"),
    )
    readonly_fields = ("date_created", "updated_at", "active_session", "last_login")
    extra = 0
