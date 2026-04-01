from django.urls import path
from django.views.generic.base import RedirectView

urlpatterns = [
    path(
        "",
        RedirectView.as_view(
            url="https://app.mosquitoalert.com/messages", permanent=True
        ),
        name="notifications",
    ),
    path(
        "list/",
        RedirectView.as_view(
            url="https://app.mosquitoalert.com/messages", permanent=True
        ),
        name="notifications_table",
    ),
    path(
        "detail/<int:notification_id>",
        RedirectView.as_view(
            url="https://app.mosquitoalert.com/messages/%(notification_id)s/",
            permanent=True,
        ),
        name="notification_detail",
    ),
]
