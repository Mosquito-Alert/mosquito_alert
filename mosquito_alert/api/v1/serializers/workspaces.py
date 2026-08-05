from rest_framework import serializers

from mosquito_alert.api.v1.serializers.countries import CountrySerializer
from mosquito_alert.api.v1.serializers.users import SimpleUserSerializer
from mosquito_alert.workspaces.models import (
    Workspace,
    WorkspaceCollaborationGroup,
    WorkspaceMembership,
)


class WorkspaceSerializer(serializers.ModelSerializer):
    class WorkspaceMembershipSerializer(serializers.ModelSerializer):
        user = SimpleUserSerializer(read_only=True)

        class Meta:
            model = WorkspaceMembership
            fields = ("user", "role", "created_at")
            extra_kwargs = {
                "created_at": {"read_only": True},
            }

    memberships = WorkspaceMembershipSerializer(many=True, read_only=True)
    country = CountrySerializer(allow_null=True, read_only=True)

    class Meta:
        model = Workspace
        fields = (
            "id",
            "name",
            "country",
            "memberships",
            "is_public",
            "supervisor_exclusivity_days",
            "updated_at",
        )
        extra_kwargs = {
            "updated_at": {"read_only": True},
        }


class SimpleWorkspaceSerializer(WorkspaceSerializer):
    class Meta:
        model = Workspace
        fields = ("id", "name", "country")


class WorkspaceCollaborationGroupSerializer(serializers.ModelSerializer):
    reviewers = SimpleUserSerializer(many=True, read_only=True)
    workspaces = SimpleWorkspaceSerializer(many=True, read_only=True)

    class Meta:
        model = WorkspaceCollaborationGroup
        fields = ("id", "name", "workspaces", "reviewers", "created_at", "updated_at")
        extra_kwargs = {
            "created_at": {"read_only": True},
            "updated_at": {"read_only": True},
        }
