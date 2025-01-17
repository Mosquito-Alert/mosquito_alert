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

    def has_prediction(self, state: bool = True):
        return self.filter(prediction__isnull=not state)

        from .models import ObservationPrediction
        return self.annotate(
            prediction_exist=models.Exists(
                ObservationPrediction.objects.filter(report=models.OuterRef('pk'))
            )
        ).filter(prediction_exist=state)

    def has_predictions_all_photos(self, state: bool = True):
        # Annotate the Report model with counts of photos and photos with predictions
        annotated_queryset = self.has_photos().annotate(
            total_photos=models.Count('photos'),  # Count total photos in the report
            photos_with_predictions=models.Count('photos__prediction')  # Count photos with predictions
        )

        if state:
            # When state is True, ensure all photos have predictions
            return annotated_queryset.filter(
                total_photos=models.F('photos_with_predictions')  # Ensure all photos have predictions
            )
        else:
            # When state is False, allow even if one photo does not have a prediction
            return annotated_queryset.filter(
                total_photos__gt=models.F('photos_with_predictions')  # If not all photos have predictions
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
                models.Q(map_aux_report__isnull=False)
                & ~models.Q(map_aux_report__private_webmap_layer__in=PRIVATE_LAYERS),
                _negated=not state
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