from django.db import models

class ReportQuerySet(models.QuerySet):
    def deleted(self, state: bool = True):
        return self.exclude(deleted_at__isnull=state)

    def non_deleted(self):
        return self.deleted(state=False)

ReportManager = models.Manager.from_queryset(ReportQuerySet)
