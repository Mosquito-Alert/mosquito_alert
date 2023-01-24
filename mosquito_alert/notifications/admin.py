from django.contrib import admin

from .models import NotificationSubscription


class NotificationSubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        "subscribed_actor",
        "subscribed_target",
        "level",
        "user",
        "created_at",
    ]
    list_filter = ["user"]


admin.site.register(NotificationSubscription, NotificationSubscriptionAdmin)
