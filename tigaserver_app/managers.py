from django.db import models
from django.db.models.query import QuerySet
from django.utils import timezone

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
        return self.filter(deleted_at__isnull=not state)

    def non_deleted(self):
        return self.deleted(state=False)
    
    def published(self, state: bool = True):
        return self.browsable().filter(
            models.Q(
                published_at__isnull=False,
                published_at__lte=timezone.now(),
                _negated=not state
            )
        )

    def browsable(self):
        # Should be the same as in is_browsable property.
        return self.non_deleted().filter(
            hide=False,
            location_is_masked=False
        ).exclude(
            tags__name="345"
        )

    def with_finished_validation(self, state: bool = True) -> QuerySet:
        from tigacrafting.models import IdentificationTask
        return self.filter(
            models.Q(
                identification_tasks__status=IdentificationTask.Status.DONE,
                _negated=not state
            )
        )

    def in_supervised_country(self, state: bool = True) -> QuerySet:
        from tigacrafting.models import UserStat

        return self.annotate(
            _in_supervised_country=models.Exists(
                UserStat.objects.filter(
                    national_supervisor_of__isnull=False,
                    national_supervisor_of=models.OuterRef('country')
                )
            ),
        ).filter(
            models.Q(
                models.Q(
                    country__isnull=False,
                    _in_supervised_country=True
                ),
                _negated=not state
            )
        )

    def in_coarse_filter(self) -> QuerySet:
        from tigacrafting.models import ExpertReportAnnotation

        return self.browsable().has_photos().exclude(
            models.Exists(
                ExpertReportAnnotation.objects.filter(report_id=models.OuterRef('pk'))
            )
        ).order_by('-server_upload_time')

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
