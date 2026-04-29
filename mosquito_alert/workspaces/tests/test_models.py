import pytest

from django.db import models
from django.db.utils import IntegrityError

from mosquito_alert.geo.tests.factories import EuropeCountryFactory
from mosquito_alert.users.tests.factories import create_regular_user

from ..models import Workspace, WorkspaceMembership, WorkspaceCollaborationGroup

from .factories import WorkspaceFactory


@pytest.mark.django_db
class TestWorkspace:
    # fields
    def test_country_fk_is_unique(self):
        assert Workspace._meta.get_field("country").unique

    def test_country_cannot_be_null(self):
        assert not Workspace._meta.get_field("country").null

    def test_country_cannot_be_blank(self):
        assert not Workspace._meta.get_field("country").blank

    def test_country_is_PROTECTED(self):
        _on_delete = Workspace._meta.get_field("country").remote_field.on_delete
        assert _on_delete == models.PROTECT

    def test_country_related_name(self):
        assert (
            Workspace._meta.get_field("country").remote_field.related_name
            == "workspace"
        )

    def test_members_related_name(self):
        assert (
            Workspace._meta.get_field("members").remote_field.related_name
            == "workspaces"
        )

    def test_is_public_default(self):
        assert Workspace._meta.get_field("is_public").default

    def test_supervisor_exclusivity_days_default(self):
        assert Workspace._meta.get_field("supervisor_exclusivity_days").default == 14

    # meta
    def test_unique_for_country(self):
        country = EuropeCountryFactory()
        with pytest.raises(IntegrityError, match=r"unique constraint"):
            _ = WorkspaceFactory.create_batch(
                size=2,
                country=country,
            )


@pytest.mark.django_db
class TestWorkspaceMembership:
    # fields
    def test_workspace_cannot_be_null(self):
        assert not WorkspaceMembership._meta.get_field("workspace").null

    def test_workspace_cannot_be_blank(self):
        assert not WorkspaceMembership._meta.get_field("workspace").blank

    def test_workspace_is_CASCADE(self):
        _on_delete = WorkspaceMembership._meta.get_field(
            "workspace"
        ).remote_field.on_delete
        assert _on_delete == models.CASCADE

    def test_workspace_related_name(self):
        assert (
            WorkspaceMembership._meta.get_field("workspace").remote_field.related_name
            == "memberships"
        )

    def test_user_cannot_be_null(self):
        assert not WorkspaceMembership._meta.get_field("user").null

    def test_user_cannot_be_blank(self):
        assert not WorkspaceMembership._meta.get_field("user").blank

    def test_user_is_CASCADE(self):
        _on_delete = WorkspaceMembership._meta.get_field("user").remote_field.on_delete
        assert _on_delete == models.CASCADE

    def test_user_related_name(self):
        assert (
            WorkspaceMembership._meta.get_field("user").remote_field.related_name
            == "workspace_memberships"
        )

    def test_role_cannot_be_null(self):
        assert not WorkspaceMembership._meta.get_field("role").null

    def test_role_cannot_be_blank(self):
        assert not WorkspaceMembership._meta.get_field("role").blank

    def test_role_default_is_memeber(self):
        assert (
            WorkspaceMembership._meta.get_field("role").default
            == WorkspaceMembership.Role.MEMBER
        )

    def test_role_is_db_index(self):
        assert WorkspaceMembership._meta.get_field("role").db_index

    def test_created_at_auto_now_add(self):
        assert WorkspaceMembership._meta.get_field("created_at").auto_now_add
        assert not WorkspaceMembership._meta.get_field("created_at").editable

    # meta
    def test_unique_user_workspace(self):
        workspace = WorkspaceFactory()
        user = create_regular_user()
        workspace.members.add(user)
        with pytest.raises(IntegrityError, match=r"unique constraint"):
            _ = WorkspaceMembership.objects.create(workspace=workspace, user=user)


@pytest.mark.django_db
class TestWorkspaceCollaborationGroup:
    # fields
    def test_workspaces_related_name(self):
        assert (
            WorkspaceCollaborationGroup._meta.get_field(
                "workspaces"
            ).remote_field.related_name
            == "collaboration_groups"
        )

    def test_reviewers_related_name(self):
        assert (
            WorkspaceCollaborationGroup._meta.get_field(
                "reviewers"
            ).remote_field.related_name
            == "collaboration_groups"
        )

    def test_name_cannot_be_null(self):
        assert not WorkspaceCollaborationGroup._meta.get_field("name").null

    def test_name_cannot_be_blank(self):
        assert not WorkspaceCollaborationGroup._meta.get_field("name").blank

    def test_name_unique(self):
        assert WorkspaceCollaborationGroup._meta.get_field("name").unique

    def test_created_at_auto_now_add(self):
        assert WorkspaceCollaborationGroup._meta.get_field("created_at").auto_now_add
        assert not WorkspaceCollaborationGroup._meta.get_field("created_at").editable

    def test_updated_at_auto_now(self):
        assert WorkspaceCollaborationGroup._meta.get_field("updated_at").auto_now
        assert not WorkspaceCollaborationGroup._meta.get_field("updated_at").editable
