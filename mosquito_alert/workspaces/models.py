from django.db import models
from django.contrib.auth import get_user_model

from mosquito_alert.geo.models import EuropeCountry

User = get_user_model()


class Workspace(models.Model):
    country = models.OneToOneField(
        EuropeCountry, on_delete=models.PROTECT, related_name="workspace"
    )
    members = models.ManyToManyField(
        User,
        through="WorkspaceMembership",
        related_name="workspaces",
        help_text="Users who can access the workspace.",
    )

    is_public = models.BooleanField(
        default=True,
        help_text="Whether the results of the workspace are visible to the public.",
    )

    supervisor_exclusivity_days = models.IntegerField(
        default=14,
        help_text="Number of days that a identification tasks in the queue is exclusively available to the supervisors.",
    )

    updated_at = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return f"{self.country.name_engl} workspace"


class WorkspaceMembership(models.Model):
    class Role(models.TextChoices):
        MEMBER = "member", "Member"
        ANNOTATOR = "annotator", "Annotator"
        SUPERVISOR = "supervisor", "Supervisor"

    workspace = models.ForeignKey(
        Workspace, on_delete=models.CASCADE, related_name="memberships"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="workspace_memberships"
    )

    role = models.CharField(
        max_length=16, choices=Role.choices, default=Role.MEMBER, db_index=True
    )

    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "workspace"], name="unique_workspace_membership"
            )
        ]


class WorkspaceCollaborationGroup(models.Model):
    workspaces = models.ManyToManyField(
        Workspace,
        related_name="collaboration_groups",
        help_text="Workspaces that can collaborate with each other within this group.",
    )
    # NOTE: in a future this might be converted to a through model if we want to have different user roles
    reviewers = models.ManyToManyField(
        User,
        related_name="collaboration_groups",
    )

    name = models.CharField(max_length=255, unique=True)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
