from datetime import timedelta
from typing import Optional, List, Union

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.functions import Coalesce
from django.db.models.query import QuerySet
from django.utils import timezone

from mosquito_alert.geo.models import EuropeCountry
from mosquito_alert.users.models import TigaUser, UserStat
from mosquito_alert.workspaces.models import (
    Workspace,
    WorkspaceMembership,
    WorkspaceCollaborationGroup,
)


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
    """

    # STAGES QUERYSETS
    def new(self) -> QuerySet:
        """Never assigned, not yet in the annotation process."""
        from .models import IdentificationTask

        return self.filter(status=IdentificationTask.Status.OPEN, total_annotations=0)

    def backlog(self, user: User) -> QuerySet:
        """Awaiting assignment but part of the annotation cycle for this user."""
        from .models import IdentificationTask

        qs = self._assignable()

        if not isinstance(user, User):
            return qs.none()

        userstat: Optional[UserStat] = None
        try:
            userstat = user.userstat
        except UserStat.DoesNotExist:
            pass
        has_role_view_perm = userstat and userstat.has_role_permission_by_model(
            action="view", model=IdentificationTask, country=None
        )
        if has_role_view_perm:
            # Has global view permission, can see all tasks.
            return qs

        qs = qs.exclude(assignees=user)

        user_workspace_qs = Workspace.objects.filter(memberships__user=user)

        workspace_id_subquery = (
            Workspace.objects.annotate(
                report_country_id=models.ExpressionWrapper(
                    models.OuterRef(models.OuterRef("report__country")),
                    output_field=models.IntegerField(),
                )
            )
            .filter(
                models.Q(country=models.F("report_country_id"))
                | models.Q(country__isnull=True, report_country_id__isnull=True)
            )
            .values("pk")[:1]
        )

        # Prioritize tasks by:
        # 1. Tasks from user's workspace where they have permissions (supervisor or annotator)
        # 2. Tasks from other workspaces but from the same identification pool.
        # 3. Tasks from other countries without identification pool
        qs = (
            qs.annotate(
                in_user_nuts2=models.Case(
                    models.When(
                        report__nuts_2_fk__isnull=False,
                        report__nuts_2_fk_id=userstat.nuts2_assignation_id
                        if userstat
                        else None,
                        then=models.Value(True),
                    ),
                    default=models.Value(False),
                    output_field=models.BooleanField(),
                ),
                in_user_workspace=models.Exists(
                    user_workspace_qs.filter(pk=models.Subquery(workspace_id_subquery))
                ),
                in_supervised_user_workspace=models.Exists(
                    WorkspaceMembership.objects.filter(
                        user=user,
                        role=WorkspaceMembership.Role.SUPERVISOR,
                        workspace_id=models.Subquery(workspace_id_subquery),
                    )
                ),
                in_user_workspace_collaboration_group=models.Exists(
                    WorkspaceCollaborationGroup.objects.filter(
                        workspaces=models.Subquery(workspace_id_subquery)
                    ).filter(
                        models.Q(workspaces__in=user_workspace_qs)
                        | models.Q(
                            pk__in=user.collaboration_groups_as_reviewer.values("pk")
                        )
                    )
                ),
            )
            .annotate_exclusivity_period()
            .filter(
                models.Q(_in_exclusivity_period=False)
                | models.Q(
                    _in_exclusivity_period=True,
                    in_supervised_user_workspace=True,
                )
            )
            .filter(
                models.Q(in_user_workspace=True)
                | models.Q(in_user_workspace_collaboration_group=True)
            )
            .annotate(
                priority=models.Case(
                    models.When(_in_exclusivity_period=True, then=models.Value(4)),
                    models.When(in_user_nuts2=True, then=models.Value(3)),
                    models.When(in_user_workspace=True, then=models.Value(2)),
                    models.When(
                        in_user_workspace_collaboration_group=True, then=models.Value(1)
                    ),
                    default=models.Value(0),
                    output_field=models.IntegerField(),
                )
            )
        )

        return qs.order_by(
            # NOTE: ordering by report__server_upload_time instead of the created_at from IdentificationTask.
            #      To be discussed. Keeping like this for legacy reasons now.
            "-priority",
            "-report__server_upload_time",
        )

    def ongoing(self) -> QuerySet:
        "Any task that has entered the annotation cycle"
        from .models import IdentificationTask

        return self.filter(
            status=IdentificationTask.Status.OPEN, total_annotations__gt=0
        )

    def blocked(self, days: int = settings.ENTOLAB_LOCK_PERIOD) -> QuerySet:
        from .models import ExpertReportAnnotation

        return (
            self.ongoing()
            ._assignable(False)
            .filter(
                models.Exists(
                    ExpertReportAnnotation.objects.stale(days=days).filter(
                        identification_task=models.OuterRef("pk"),
                    )
                )
            )
        )

    def annotating(self) -> QuerySet:
        "Being actively labeled by experts."
        return self.ongoing().exclude(
            total_annotations=models.F("total_finished_annotations")
        )

    def to_review(self) -> QuerySet:
        "Annotations completed, waiting for reviewer"
        from .models import IdentificationTask

        return self.filter(
            models.Q(status=IdentificationTask.Status.CONFLICT)
            | models.Q(status=IdentificationTask.Status.REVIEW)
            | models.Q(status=IdentificationTask.Status.DONE, reviewed_at__isnull=True)
        )

    def closed(self) -> QuerySet:
        from .models import IdentificationTask

        return self.filter(status__in=IdentificationTask.CLOSED_STATUS)

    def done(self, state: bool = True) -> QuerySet:
        from .models import IdentificationTask

        return self.filter(
            models.Q(status=IdentificationTask.Status.DONE, _negated=not state)
        )

    # SUPPORTING QUERYSETS
    def annotate_exclusivity_period(self) -> QuerySet:
        from .models import IdentificationTask

        return self.annotate(
            country_has_supervisor=models.Exists(
                WorkspaceMembership.objects.filter(
                    role=WorkspaceMembership.Role.SUPERVISOR,
                    workspace__country=models.OuterRef("report__country"),
                )
            ),
            supervisor_has_annotated=models.Case(
                models.When(
                    country_has_supervisor=True,
                    then=models.Exists(
                        IdentificationTask.objects.supervisor_has_annotated().filter(
                            pk=models.OuterRef("pk")
                        )
                    ),
                ),
                default=models.Value(False),
                output_field=models.BooleanField(),
            ),
            # NOTE: using "_" not to raise error due to same name is used for a @property.
            _exclusivity_end=models.Case(
                models.When(
                    models.Q(status=IdentificationTask.Status.OPEN),
                    then=models.ExpressionWrapper(
                        models.F("report__server_upload_time")
                        + Coalesce(
                            # TODO: what if two workspaces? max or min?
                            models.F(
                                "report__country__workspace__supervisor_exclusivity_days"
                            ),
                            models.Value(0),
                        )
                        * models.Value(timedelta(days=1)),
                        output_field=models.DateTimeField(),
                    ),
                ),
                default=models.Value(None),
                output_field=models.DateTimeField(),
            ),
            # NOTE: using "_" not to raise error due to same name is used for a @property.
            _in_exclusivity_period=models.Q(
                models.Q(country_has_supervisor=True)
                & models.Q(
                    _exclusivity_end__isnull=False, _exclusivity_end__gt=timezone.now()
                )
                & models.Q(supervisor_has_annotated=False)
            ),
        )

    def in_exclusivity_period(self, state: bool = True) -> QuerySet:
        return self.annotate_exclusivity_period().filter(_in_exclusivity_period=state)

    def supervisor_has_annotated(self, state: bool = True) -> QuerySet:
        from .models import ExpertReportAnnotation

        return self.annotate(
            supervisor_has_annotated=models.Exists(
                ExpertReportAnnotation.objects.filter(
                    identification_task=models.OuterRef("pk"),
                    is_finished=True,
                    user__in=WorkspaceMembership.objects.filter(
                        role=WorkspaceMembership.Role.SUPERVISOR,
                        workspace__country=models.OuterRef(
                            "identification_task__report__country"
                        ),
                    ).values("user"),
                )
            )
        ).filter(supervisor_has_annotated=state)

    def annotated_by(self, users: List[User]) -> QuerySet:
        from .models import ExpertReportAnnotation

        return self.filter(
            models.Exists(
                ExpertReportAnnotation.objects.completed().filter(
                    identification_task=models.OuterRef("pk"),
                    user__in=users,
                )
            )
        )

    def assigned_to(self, users: List[User]) -> QuerySet:
        from .models import ExpertReportAnnotation

        return self.filter(
            models.Exists(
                ExpertReportAnnotation.objects.filter(
                    identification_task=models.OuterRef("pk"), user__in=users
                )
            )
        )

    def _assignable(self, state: bool = True) -> QuerySet:
        # NOTE: Private method. Do not use outside this class.
        from .models import IdentificationTask

        return self.filter(
            models.Q(
                status=IdentificationTask.Status.OPEN,
                total_annotations__lt=settings.MAX_N_OF_EXPERTS_ASSIGNED_PER_REPORT,
                _negated=not state,
            )
        )

    # OTHER QUERYSETS
    def browsable(self, user: Union[User, TigaUser]) -> QuerySet:
        from .models import IdentificationTask

        qs = self

        if not isinstance(user, User):
            return qs.none()

        view_archived_perm = "%(app_label)s.view_archived_identificationtasks" % {
            "app_label": IdentificationTask._meta.app_label,
        }
        # Exclude archived tasks unless user is a full User and has permission
        if not user.has_perm(view_archived_perm):
            qs = qs.exclude(status=IdentificationTask.Status.ARCHIVED)

        userstat: Optional[UserStat] = None
        try:
            userstat = user.userstat
        except UserStat.DoesNotExist:
            pass
        has_role_view_perm = userstat and userstat.has_role_permission_by_model(
            action="view", model=IdentificationTask, country=None
        )
        if has_role_view_perm:
            # Has global view permission, can see all tasks.
            return qs

        result_qs = self.annotated_by(users=[user])
        # Filter by countries if user has region-specific permissions
        if userstat:
            country_lookup = models.Q()
            view_countries = (
                userstat.get_countries_with_permissions(
                    action="view", model=IdentificationTask
                )
                if userstat
                else []
            )
            if view_countries:
                country_lookup |= models.Q(report__country__in=view_countries)

            country_workspace_member = EuropeCountry.objects.filter(
                workspace__members=user
            ).distinct()
            if country_workspace_member:
                country_lookup |= models.Q(
                    report__country__in=country_workspace_member,
                    status=IdentificationTask.Status.DONE,
                )

            if country_lookup:
                result_qs |= qs.filter(country_lookup)

        return result_qs


IdentificationTaskManager = models.Manager.from_queryset(IdentificationTaskQuerySet)


class ExpertReportAnnotationQuerySet(models.QuerySet):
    def completed(self, state: bool = True) -> QuerySet:
        return self.filter(is_finished=state)

    def stale(self, days: int = settings.ENTOLAB_LOCK_PERIOD) -> QuerySet:
        return self.filter(
            is_finished=False,
            created__lte=timezone.now() - timedelta(days=days),
        )

    def blocking(self) -> QuerySet:
        from .models import IdentificationTask

        return self.stale().filter(
            identification_task__in=IdentificationTask.objects.blocked()
        )


ExpertReportAnnotationManager = models.Manager.from_queryset(
    ExpertReportAnnotationQuerySet
)
