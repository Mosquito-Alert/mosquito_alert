from datetime import timedelta
from typing import Optional

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.functions import Coalesce
from django.db.models.query import QuerySet
from django.utils import timezone

class IdentificationTaskQuerySet(models.QuerySet):
    """
    QuerySet for IdentificationTask model providing querysets to filter tasks based on their 
    annotation lifecycle, user role, and assignment rules.

    Available querysets:
    - `new()`: Retrieves tasks that have never been assigned and are not yet in the annotation process.
    - `backlog(user)`: Retrieves tasks awaiting assignment but part of the annotation cycle, prioritizing based on user attributes.
    - `ongoing()`: Retrieves tasks that have entered the annotation cycle and have at least one annotation.
    - `blocked(days)`: Retrieves tasks that are ongoing but blocked due to inactivity of annotators.
    - `annotating()`: Retrieves tasks currently being annotated but not yet fully completed.
    - `to_review()`: Retrieves tasks that have completed annotations but require review.
    - `closed()`: Retrieves tasks that have been finalized and closed.
    - `done(state)`: Retrieves tasks marked as done, with the ability to toggle negation.

    The `backlog` method is particularly complex as it prioritizes tasks based on user role:
    - Bounding Box users are assigned tasks from their native country.
    - European users prioritize tasks from their own country, then general European tasks.
    - Spanish users prioritize tasks from their NUTS2 region, then Spain, then Europe.
    - National supervisors can access tasks under exclusivity periods for their assigned country.
    """

    # STAGES QUERYSETS
    def new(self) -> QuerySet:
        """Never assigned, not yet in the annotation process."""
        from .models import IdentificationTask
        return self.filter(
            status=IdentificationTask.Status.OPEN,
            total_annotations=0
        )

    def backlog(self, user: Optional[User] = None) -> QuerySet:
        """Awaiting assignment but part of the annotation cycle."""
        from tigaserver_app.models import EuropeCountry, Report

        qs = self._assignable()

        if not user:
            return qs

        # Filter and prioritize tasks for the user
        qs = qs.exclude(assignees=user).annotate(
            in_supervised_country=models.Exists(
                Report.objects.filter(
                    identification_task=models.OuterRef('pk')
                ).in_supervised_country()
            )
        #NOTE: ordering by report__server_upload_time instead of the created_at from IdentificationTask.
        #      To be discussed. Keeping like this for legacy reasons now.
        ).order_by("-in_supervised_country", "-report__server_upload_time")

        # Start pioritization:
        # Summary:
        # - Case user in bounding box:
        #       1. Report.country is the bounding box
        # - Other (expert and national supervisor):
        #       1. Report.country is not bounding box
        #       2. Report is not in the exclusivity period (except for its country if user is national supervisor)
        #       3. Sort by:
        #           European user:
        #               1. Report is in europe
        #               2. Report is user's country
        #               3. Append default ordering
        #           Spanish user:
        #               1. Report is in spain and nuts2 region
        #               2. Report is in spain
        #               3. Report is in europe
        #               4. Append default ordering
        if user.userstat.is_bb_user():
            # Case user in a bounding box
            return qs.filter(
                report__country=user.userstat.native_of
            )

        # Case regular user (expert and national supervisors)
        qs = qs.filter(
            report__country__is_bounding_box=False
        )

        # Case regular expert user
        qs = qs.in_exclusivity_period(state=False)

        # Prioritize for user
        if user.groups.filter(name='eu_group_europe').exists():
            # Case European user: Prioritize reports from own country
            qs = qs.annotate(
                in_user_country=models.Case(
                    models.When(
                        report__country=user.userstat.national_supervisor_of or user.userstat.native_of,
                        then=True
                    ),
                    default=False,
                    output_field=models.BooleanField()
                )
            ).order_by(
                # NOTE: appending here all the field to be ordered_by since order_by function
                #       can not be chained, and each order_by cal will clear any previous ordering.
                *(
                    ('-in_user_country',) + qs.query.order_by
                )
            )
        else:
            # Case Non European user: Prioritize reports from nuts2 assignation, then spain, the Europe.
            spain_country = EuropeCountry.objects.spain()
            qs = qs.annotate(
                in_spain_own_region=models.Case(
                    models.When(
                        models.Q(
                            report__country=spain_country,
                            report__nuts_2=user.userstat.nuts2_assignation.nuts_id if user.userstat.nuts2_assignation else None
                        ),
                        then=True
                    ),
                    default=False,
                    output_field=models.BooleanField()
                ),
                in_spain=models.Case(
                    models.When(
                        report__country=spain_country,
                        then=True
                    ),
                    default=False,
                    output_field=models.BooleanField()
                ),
                in_europe=models.Case(
                    models.When(
                        report__country__isnull=False,
                        then=True
                    ),
                    default=False,
                    output_field=models.BooleanField()
                )
            ).order_by(
                # NOTE: appending here all the field to be ordered_by since order_by function
                #       can not be chained, and each order_by cal will clear any previous ordering.
                *(
                    ('-in_spain_own_region', '-in_spain', '-in_europe') + qs.query.order_by
                )
            )

        if user.userstat.national_supervisor_of:
            # Case national supervisor
            qs_in_exclusivity = self._assignable().exclude(assignees=user).filter(
                report__country=user.userstat.national_supervisor_of
            ).in_exclusivity_period(state=True)

            qs = qs.annotate(
                in_exclusivty=models.Value(False, output_field=models.BooleanField())
            )
            qs_in_exclusivity = qs_in_exclusivity.annotate(
                in_exclusivty=models.Value(True, output_field=models.BooleanField())
            )

            qs = qs | qs_in_exclusivity
            qs.order_by(
                *(
                    ('-in_exclusivty', ) + qs.query.order_by
                )
            )

        return qs

    def ongoing(self) -> QuerySet:
        "Any task that has entered the annotation cycle"
        from .models import IdentificationTask
        return self.filter(
            status=IdentificationTask.Status.OPEN,
            total_annotations__gt=0
        )

    def blocked(self, days: int = settings.ENTOLAB_LOCK_PERIOD)  -> QuerySet:
        from .models import ExpertReportAnnotation

        return self.ongoing()._assignable(False).filter(
            models.Exists(
                ExpertReportAnnotation.objects.stale(days=days).filter(
                    identification_task=models.OuterRef('pk'),
                ).exclude(
                    user__groups__name='superexpert'
                )
            )
        )

    def annotating(self) -> QuerySet:
        "Being actively labeled by experts."
        return self.ongoing().exclude(
            total_annotations=models.F('total_finished_annotations')
        )

    def to_review(self) -> QuerySet:
        "Annotations completed, waiting for reviewer"
        from .models import IdentificationTask
        return self.filter(
            models.Q(status=IdentificationTask.Status.CONFLICT)
            | models.Q(status=IdentificationTask.Status.FLAGGED)
            | models.Q(status=IdentificationTask.Status.REVIEW)
        )

    def closed(self) -> QuerySet:
        from .models import IdentificationTask
        return self.filter(
            status__in=IdentificationTask.CLOSED_STATUS
        )

    def done(self, state: bool = True) -> QuerySet:
        from .models import IdentificationTask
        return self.filter(
            models.Q(
                status=IdentificationTask.Status.DONE,
                _negated=not state
            )
        )

    # SUPPORTING QUERYSETS
    def in_exclusivity_period(self, state: bool = True) -> QuerySet:
        from tigaserver_app.models import Report
        from .models import IdentificationTask

        qs = self.filter(
            status=IdentificationTask.Status.OPEN
        ).annotate(
            in_supervised_country=models.Exists(
                Report.objects.filter(identification_task=models.OuterRef('pk')).in_supervised_country()
            ),
            supervisor_has_annotated=models.Exists(
                IdentificationTask.objects.supervisor_has_annotated().filter(pk=models.OuterRef('pk'))
            ),
            # NOTE: using "_" not to raise error due to same name is used for a @property.
            _exclusivity_end=models.ExpressionWrapper(
                models.F("report__server_upload_time") +
                Coalesce(
                    models.F("report__country__national_supervisor_report_expires_in"),
                    models.Value(0)
                ) * models.Value(timedelta(days=1)),
                output_field=models.DateTimeField(),
            )
        )

        return qs.filter(
            models.Q(
                models.Q(in_supervised_country=True)
                & models.Q(_exclusivity_end__gt=timezone.now())
                & models.Q(supervisor_has_annotated=False),
                _negated=not state
            )
        )

    def supervisor_has_annotated(self, state: bool = True) -> QuerySet:
        from tigaserver_app.models import Report
        from .models import ExpertReportAnnotation

        return self.filter(
            report__in=Report.objects.filter(identification_task__isnull=False).in_supervised_country()
        ).annotate(
            supervisor_has_annotated=models.Exists(
                ExpertReportAnnotation.objects.filter(
                    identification_task=models.OuterRef('pk'),
                    validation_complete=True,
                    user__userstat__national_supervisor_of__isnull=False,
                    user__userstat__national_supervisor_of=models.OuterRef('report__country'),
                )
            )
        ).filter(
            supervisor_has_annotated=state
        )

    def annotated_by(self, user: User, state: bool = True) -> QuerySet:
        from .models import ExpertReportAnnotation

        return self.annotate(
            user_has_annotated=models.Exists(
                ExpertReportAnnotation.objects.filter(
                    identification_task=models.OuterRef('pk'),
                    user=user,
                    validation_complete=True,
                )
            )
        ).filter(
            user_has_annotated=state
        )

    def _assignable(self, state: bool = True) -> QuerySet:
        # NOTE: Private method. Do not use outside this class.
        from .models import IdentificationTask

        return self.filter(
            models.Q(
                status=IdentificationTask.Status.OPEN,
                total_annotations__lt=settings.MAX_N_OF_EXPERTS_ASSIGNED_PER_REPORT,
                _negated=not state
            )
        )

IdentificationTaskManager = models.Manager.from_queryset(IdentificationTaskQuerySet)

class ExpertReportAnnotationQuerySet(models.QuerySet):
    def completed(self, state: bool = True) -> QuerySet:
        return self.filter(validation_complete=state)

    def stale(self, days: int = settings.ENTOLAB_LOCK_PERIOD) -> QuerySet:
        return self.filter(
            validation_complete=False,
            created__lte=timezone.now() - timedelta(days=days),
        )

ExpertReportAnnotationManager = models.Manager.from_queryset(ExpertReportAnnotationQuerySet)