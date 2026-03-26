from django.db import models

from mosquito_alert.users.models import TigaUser


class NotificationQuerySet(models.QuerySet):
    def for_user(self, user: TigaUser):
        from .models import NotificationTopic

        topics = NotificationTopic.objects.filter(
            models.Q(topic_users__user=user) | models.Q(topic_code="global")
        ).distinct()

        return self.filter(
            models.Q(user=user)
            |
            # models.Q(report__user=user) |
            models.Q(notification_sendings__sent_to_user=user)
            | models.Q(notification_sendings__sent_to_topic__in=topics)
        )

    def seen_by_user(self, user: TigaUser, state: bool = True):
        return self.filter(
            models.Q(
                models.Q(notification_acknowledgements__user=user)
                | models.Q(user=user, acknowledged=True),
                _negated=not state,
            )
        )


NotificationManager = models.Manager.from_queryset(NotificationQuerySet)
