from django.db import models

class ReportQuerySet(models.QuerySet):

    def __version_subquery(self):
        # NOTE: need to force using "objects" (default manager)
        return self.model._default_manager.filter(
            user=models.OuterRef('user'), 
            report_id=models.OuterRef('report_id'), 
            type=models.OuterRef('type')
        )

    def __latest_version_subquery(self):
        return self.__version_subquery().order_by('-version_number', '-server_upload_time')

    def last_version_of_each(self, state: bool=True):
        return self.filter(
            models.Q(
                pk__in=models.Subquery(
                    self.__latest_version_subquery().values('pk')[:1]
                ),
                _negated=not state
            )
        )
    
    def deleted(self, state: bool = True):
        return self.annotate(
            has_negative_version=models.Exists(
                self.__version_subquery().filter(version_number=-1).values('pk')
            )
        ).filter(
            has_negative_version=state
        )


ReportManager = models.Manager.from_queryset(ReportQuerySet)