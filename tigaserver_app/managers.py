from django.db import models

class ReportQuerySet(models.QuerySet):
    def deleted(self, state: bool = True):
        return self.exclude(deleted_at__isnull=state)

    def non_deleted(self):
        return self.deleted(state=False)

    def published(self, state: bool = True):
        return self.non_deleted().filter(map_aux_report__isnull=not state)

ReportManager = models.Manager.from_queryset(ReportQuerySet)

class NotificationQuerySet(models.QuerySet):
    def for_user(self, user: 'TigaUser'):
        from .models import SentNotification

        sent_notifications_subquery = SentNotification.objects.filter(
            notification=models.OuterRef('pk')
        ).filter(
            models.Q(sent_to_user=user) |
            models.Q(sent_to_topic__topic_code='global') |
            models.Q(sent_to_topic__topic_users__user=user)
        ).values('notification').distinct('notification')

        return self.filter(
            models.Q(user=user) | 
            #models.Q(report__user=user) | 
            models.Q(pk__in=models.Subquery(sent_notifications_subquery))
        )

    def seen_by_user(self, user: 'TigaUser', state: bool = True):
        return self.filter(
            models.Q(
                models.Q(
                    notification_acknowledgements__user=user
                ) | models.Q(
                    user=user,
                    acknowledged=True
                ),
                _negated=not state
            )
        )

NotificationManager = models.Manager.from_queryset(NotificationQuerySet)
