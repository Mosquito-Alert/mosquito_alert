from django.db import models
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin

from mosquito_alert.api.v1.permissions import (
    DjangoRegularUserModelPermissions,
    FullDjangoObjectPermissions,
)
from mosquito_alert.api.v1.serializers.workspaces import (
    WorkspaceCollaborationGroupSerializer,
    WorkspaceSerializer,
)
from mosquito_alert.api.v1.views.viewsets import GenericViewSet
from mosquito_alert.utils.rules import has_global_permission
from mosquito_alert.workspaces.models import Workspace, WorkspaceCollaborationGroup


@method_decorator(
    [vary_on_headers("Authorization"), cache_page(6 * 60 * 60)], name="list"
)
@method_decorator(
    [vary_on_headers("Authorization"), cache_page(6 * 60 * 60)], name="retrieve"
)
class WorkspaceViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    queryset = (
        Workspace.objects.all()
        .select_related("country")
        .prefetch_related("memberships", "memberships__user")
    )
    serializer_class = WorkspaceSerializer
    permission_classes = (FullDjangoObjectPermissions,)

    def get_queryset(self):
        qs = super().get_queryset()

        if has_global_permission(Workspace, type="view")(user=self.request.user):
            return qs

        return qs.filter(members=self.request.user)


@extend_schema_view(
    list=extend_schema(
        tags=["workspaces"],
        operation_id="workspaces_list_mine",
        description="Get Current User's Workspaces",
    )
)
class MyWorkspaceViewSet(WorkspaceViewSet):
    def get_queryset(self):
        return super().get_queryset().filter(members=self.request.user)


@method_decorator(
    [vary_on_headers("Authorization"), cache_page(6 * 60 * 60)], name="list"
)
@method_decorator(
    [vary_on_headers("Authorization"), cache_page(6 * 60 * 60)], name="retrieve"
)
class WorkspaceCollaboratoratorViewSet(
    ListModelMixin, RetrieveModelMixin, GenericViewSet
):
    queryset = WorkspaceCollaborationGroup.objects.all().prefetch_related(
        "workspaces", "workspaces__country", "reviewers"
    )
    serializer_class = WorkspaceCollaborationGroupSerializer
    permission_classes = (DjangoRegularUserModelPermissions,)

    def get_queryset(self):
        qs = super().get_queryset()

        if has_global_permission(WorkspaceCollaborationGroup, type="view")(
            user=self.request.user
        ):
            return qs

        return qs.filter(
            models.Q(workspaces__members=self.request.user)
            | models.Q(reviewers=self.request.user)
        )


@extend_schema_view(
    list=extend_schema(
        tags=["workspaces"],
        operation_id="workspaces_collaborations_list_mine",
        description="Get Current User's Workspace Collaborations",
    )
)
class MyWorkspaceCollaboratoratorViewSet(WorkspaceCollaboratoratorViewSet):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                models.Q(workspaces__members=self.request.user)
                | models.Q(reviewers=self.request.user)
            )
        )
