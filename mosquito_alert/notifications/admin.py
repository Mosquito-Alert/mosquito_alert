from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "report",
        "expert",
        "date_comment",
    )
    search_fields = ["report__version_UUID", "user__user_UUID"]
