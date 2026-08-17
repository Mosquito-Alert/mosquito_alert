from django.db import models
from django.db.models import Count, Q


class NotificationRecipientQuerySet(models.QuerySet):
    def stats(self):
        result = self.aggregate(
            total=Count("id"),
            read=Count("id", filter=Q(is_read=True)),
        )

        return {
            "total": result["total"],
            "read": result["read"],
            "unread": result["total"] - result["read"],
        }


NotificationRecipientManager = models.Manager.from_queryset(
    NotificationRecipientQuerySet
)
