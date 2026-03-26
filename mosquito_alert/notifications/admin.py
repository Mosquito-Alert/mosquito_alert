from django.contrib import admin

from .models import Notification, NotificationTopic


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "report",
        "expert",
        "date_comment",
        "expert_comment",
        "expert_html",
        "photo_url",
    )
    search_fields = ["report__version_UUID", "user__user_UUID"]


@admin.register(NotificationTopic)
class NotificationTopicAdmin(admin.ModelAdmin):
    list_display = ("id", "topic_code", "topic_description", "topic_group")
    list_filter = ["topic_code", "topic_description"]
    ordering = ["id", "topic_code", "topic_description"]
