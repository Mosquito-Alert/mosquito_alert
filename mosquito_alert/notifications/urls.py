from django.urls import path

from .views import (
    notifications_version_two,
    notification_detail,
    notifications_table,
    user_notifications_datatable,
)

urlpatterns = [
    path("", notifications_version_two, name="notifications"),
    path("list/", notifications_table, name="notifications_table"),
    path(
        "apilist/",
        user_notifications_datatable,
        name="user_notifications_datatable",
    ),
    path(
        "detail/<int:notification_id>",
        notification_detail,
        name="notification_detail",
    ),
]
