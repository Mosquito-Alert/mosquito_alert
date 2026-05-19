from typing import Optional, Union

from django.contrib.auth.models import User
from django.db import models
from django.db.models.query import QuerySet
from django.utils import timezone

from mosquito_alert.geo.models import EuropeCountry
from mosquito_alert.users.models import TigaUser


class ReportQuerySet(models.QuerySet):
    def has_photos(self, state: bool = True):
        from .models import Photo

        return self.annotate(
            photo_exist=models.Exists(
                Photo.objects.filter(report=models.OuterRef("pk")).visible()
            )
        ).filter(photo_exist=state)

    def deleted(self, state: bool = True):
        return self.filter(deleted_at__isnull=not state)

    def non_deleted(self):
        return self.deleted(state=False)

    def browsable(self, user: Optional[Union[User, TigaUser]] = None) -> QuerySet:
        from .models import Report

        # Should be the same as in is_browsable property.
        qs = self.non_deleted().filter(hide=False, location_is_masked=False)

        # Published for everyone.
        published_lookup = models.Q(
            published_at__isnull=False, published_at__lte=timezone.now()
        )
        if isinstance(user, User):
            has_view_perm = user.has_perm(
                "%(app_label)s.view_%(model_name)s"
                % {
                    "app_label": Report._meta.app_label,
                    "model_name": Report._meta.model_name,
                }
            )
            if has_view_perm:
                return qs

            countries_in_workspace = EuropeCountry.objects.filter(
                workspace__members=user
            ).distinct()

            return qs.filter(
                published_lookup | models.Q(country__in=countries_in_workspace)
            )

        if isinstance(user, TigaUser):
            return qs.filter(published_lookup | models.Q(user=user))

        return qs.filter(published_lookup)

    def with_finished_validation(self, state: bool = True) -> QuerySet:
        from mosquito_alert.identification_tasks.models import IdentificationTask

        return self.filter(
            models.Q(
                identification_task__status=IdentificationTask.Status.DONE,
                _negated=not state,
            )
        )

    def in_coarse_filter(self) -> QuerySet:
        from .models import Report
        from mosquito_alert.identification_tasks.models import IdentificationTask

        return (
            self.non_deleted()
            .filter(hide=False, location_is_masked=False)
            .filter(published_at__isnull=True)
            .filter(
                models.Q(
                    models.Q(type=Report.TYPE_ADULT)
                    & models.Exists(
                        IdentificationTask.objects.filter(
                            report_id=models.OuterRef("pk")
                        ).new()
                    )
                )
                | models.Q(
                    models.Q(type=Report.TYPE_SITE)
                    & models.Exists(self.has_photos().filter(pk=models.OuterRef("pk")))
                )
            )
            .order_by("-server_upload_time")
        )


ReportManager = models.Manager.from_queryset(ReportQuerySet)


class PhotoQuerySet(models.QuerySet):
    def visible(self):
        return self.filter(hide=False)


PhotoManager = models.Manager.from_queryset(PhotoQuerySet)
