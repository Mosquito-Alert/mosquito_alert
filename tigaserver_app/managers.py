from django.db import models

from fcm_django.models import FCMDeviceQuerySet, FCMDeviceManager

class ReportQuerySet(models.QuerySet):
    def has_photos(self, state: bool = True):
        from .models import Photo

        return self.annotate(
            photo_exist=models.Exists(
                Photo.objects.filter(
                    report=models.OuterRef('pk')
                ).visible()
            )
        ).filter(
            photo_exist=state
        )

    def deleted(self, state: bool = True):
        return self.exclude(deleted_at__isnull=state)

    def non_deleted(self):
        return self.deleted(state=False)
    
    def published(self, state: bool = True):
        PRIVATE_LAYERS = [
            "breeding_site_not_yet_filtered",
            "conflict",
            "not_yet_validated",
            "trash_layer",
        ]
        return self.non_deleted().filter(
            models.Q(
                map_aux_report__private_webmap_layer__in=PRIVATE_LAYERS,
                _negated=state
            )
        )

ReportManager = models.Manager.from_queryset(ReportQuerySet)

class PhotoQuerySet(models.QuerySet):
    def visible(self):
        return self.filter(hide=False)

PhotoManager = models.Manager.from_queryset(PhotoQuerySet)

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

class DeviceQuerySet(FCMDeviceQuerySet):
    def deactivate_devices_with_error_results(self, *args, **kwargs):
        deactivated_ids = super().deactivate_devices_with_error_results(*args, **kwargs)

        self.filter(registration_id__in=deactivated_ids).update(is_logged_in=False)

        return deactivated_ids

class DeviceManager(FCMDeviceManager):
    def get_queryset(self):
        return DeviceQuerySet(self.model)