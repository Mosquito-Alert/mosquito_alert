from datetime import timedelta
from typing import Optional, List, Union

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.functions import Coalesce
from django.db.models.query import QuerySet
from django.utils import timezone

from mosquito_alert.users.models import TigaUser
from mosquito_alert.users.permissions import ReviewPermission
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

        return self.filter(status=IdentificationTask.Status.OPEN, total_annotations=0)

    def backlog(self, user: Optional[User] = None) -> QuerySet:
        """Awaiting assignment but part of the annotation cycle."""
        qs = self._assignable()

        if not user:
            return qs

        user_workspace_qs = Workspace.objects.filter(
            memberships__user=user,
            memberships__role__in=[
                WorkspaceMembership.Role.SUPERVISOR,
                WorkspaceMembership.Role.ANNOTATOR,
            ],
        )

        if not user_workspace_qs.exists():
            # If user has no workspace with permissions, return nothing
            return qs.none()

        qs = qs.exclude(assignees=user)

        # Prioritize tasks by:
        # 1. Tasks from user's workspace where they have permissions (supervisor or annotator)
        # 2. Tasks from other workspaces but from the same identification pool.
        # 3. Tasks from other countries without identification pool
        qs = (
            qs.annotate(
                in_unknown_country=models.Q(report__country__isnull=True),
                in_user_nuts2=models.Case(
                    models.When(
                        report__nuts_2_fk__isnull=False,
                        report__nuts_2_fk_id=user.userstat.nuts2_assignation_id,
                        then=models.Value(True),
                    ),
                    default=models.Value(False),
                    output_field=models.BooleanField(),
                ),
                in_user_workspace=models.Exists(
                    user_workspace_qs.filter(country=models.OuterRef("report__country"))
                ),
                in_user_workspace_collaboration_group=models.Exists(
                    WorkspaceCollaborationGroup.objects.filter(
                        workspaces__country=models.OuterRef("report__country")
                    ).filter(
                        workspaces__in=user_workspace_qs,
                    )
                ),
                has_workspace=models.Exists(
                    Workspace.objects.filter(
                        country_id=models.OuterRef("report__country_id")
                    )
                ),
            )
            .filter(
                models.Q(in_unknown_country=True)
                | models.Q(in_user_workspace=True)
                | models.Q(in_user_workspace_collaboration_group=True)
                | models.Q(has_workspace=False)
            )
            .in_exclusivity_period(state=False)
            .annotate(
                priority=models.Case(
                    models.When(in_user_nuts2=True, then=models.Value(4)),
                    models.When(in_user_workspace=True, then=models.Value(3)),
                    models.When(
                        in_user_workspace_collaboration_group=True, then=models.Value(2)
                    ),
                    models.When(has_workspace=False, then=models.Value(1)),
                    default=models.Value(0),
                    output_field=models.IntegerField(),
                )
            )
            .order_by(
                # NOTE: ordering by report__server_upload_time instead of the created_at from IdentificationTask.
                #      To be discussed. Keeping like this for legacy reasons now.
                "-priority",
                "-report__server_upload_time",
            )
        )

        countries_with_supervisor_role_qs = (
            Workspace.objects.filter(
                memberships__user=user,
                memberships__role=WorkspaceMembership.Role.SUPERVISOR,
            )
            .values("country")
            .distinct()
        )
        if countries_with_supervisor_role_qs.exists():
            # Case supervisor
            qs_in_exclusivity = (
                self._assignable()
                .exclude(assignees=user)
                .filter(report__country__in=countries_with_supervisor_role_qs)
                .in_exclusivity_period(state=True)
            )
            qs_in_exclusivity = qs_in_exclusivity.annotate(
                in_exclusivity=models.Value(True, output_field=models.BooleanField())
            )

            qs = qs.annotate(
                in_exclusivity=models.Value(False, output_field=models.BooleanField())
            )

            qs = qs | qs_in_exclusivity
            qs.order_by(*(("-in_exclusivity",) + qs.query.order_by))

        return qs

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
    def in_exclusivity_period(self, state: bool = True) -> QuerySet:
        from .models import IdentificationTask

        qs = self.filter(status=IdentificationTask.Status.OPEN).annotate(
            country_has_supervisor=models.Exists(
                WorkspaceMembership.objects.filter(
                    role=WorkspaceMembership.Role.SUPERVISOR,
                    workspace__country=models.OuterRef("report__country"),
                )
            ),
            supervisor_has_annotated=models.Exists(
                IdentificationTask.objects.supervisor_has_annotated().filter(
                    pk=models.OuterRef("pk")
                )
            ),
            # NOTE: using "_" not to raise error due to same name is used for a @property.
            _exclusivity_end=models.ExpressionWrapper(
                models.F("report__server_upload_time")
                + Coalesce(
                    models.F("report__country__workspace__supervisor_exclusivity_days"),
                    models.Value(0),
                )
                * models.Value(timedelta(days=1)),
                output_field=models.DateTimeField(),
            ),
        )

        return qs.filter(
            models.Q(
                models.Q(country_has_supervisor=True)
                & models.Q(_exclusivity_end__gt=timezone.now())
                & models.Q(supervisor_has_annotated=False),
                _negated=not state,
            )
        )

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
        from mosquito_alert.users.models import UserStat

        qs = self

        view_archived_perm = "%(app_label)s.view_archived_identificationtasks" % {
            "app_label": IdentificationTask._meta.app_label,
        }
        # Exclude archived tasks unless user is a full User and has permission
        if not user.has_perm(view_archived_perm):
            qs = qs.exclude(status=IdentificationTask.Status.ARCHIVED)

        view_perm = "%(app_label)s.view_%(model_name)s" % {
            "app_label": IdentificationTask._meta.app_label,
            "model_name": IdentificationTask._meta.model_name,
        }
        has_view_perm = user.has_perm(view_perm)

        user_role = user
        if isinstance(user, User):
            try:
                user_role = user.userstat
            except UserStat.DoesNotExist:
                user_role = None
        has_role_view_perm = user_role and user_role.has_role_permission_by_model(
            action="view", model=IdentificationTask, country=None
        )
        has_role_review_perm = user_role and user_role.has_role_permission_by_model(
            action="add", model=ReviewPermission, country=None
        )

        if has_view_perm or has_role_view_perm or has_role_review_perm:
            return qs

        if isinstance(user, User):
            # If user is a regular User, filter by their own tasks
            qs_annotated = qs.annotated_by(users=[user])
        else:
            qs_annotated = qs.none()

        # Filter by countries if user has region-specific permissions
        view_countries = (
            user_role.get_countries_with_permissions(
                action="view", model=IdentificationTask
            )
            if user_role
            else []
        )
        review_countries = (
            user_role.get_countries_with_permissions(
                action="add", model=ReviewPermission
            )
            if user_role
            else []
        )
        if countries := set(view_countries + review_countries):
            return qs_annotated | qs.filter(report__country__in=countries)

        return qs_annotated


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
