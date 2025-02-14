from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

class ExpertReportAnnotationQuerySet(models.QuerySet):

    def blocked(self, days: int = settings.ENTOLAB_LOCK_PERIOD):
        from tigaserver_app.models import Report

        # Subquery for reports with finished validation
        finished_validation_subquery = Report.objects.with_finished_validation().filter(
            pk=models.OuterRef('report_id')
        )

        return self.exclude(
            user__groups__name='superexpert',
        ).filter(
            created__lt=timezone.now() - timedelta(days=days),
            validation_complete=False
        ).exclude(
            models.Exists(finished_validation_subquery)
        )

ExpertReportAnnotationManager = models.Manager.from_queryset(ExpertReportAnnotationQuerySet)