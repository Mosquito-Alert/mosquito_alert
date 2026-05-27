from django.contrib.gis.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from mosquito_alert.geo.models import EuropeCountry

User = get_user_model()


class Workspace(models.Model):
    country = models.ForeignKey(
        EuropeCountry,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="workspaces",
    )
    geom = models.MultiPolygonField(
        null=True,
        blank=True,
        help_text="The geographical area covered by the workspace. If not specified, the workspace covers the entire country.",
    )
    members = models.ManyToManyField(
        User,
        through="WorkspaceMembership",
        related_name="workspaces",
        help_text="Users who can access the workspace.",
    )

    name = models.CharField(max_length=255, null=True, blank=True)

    is_public = models.BooleanField(
        default=True,
        help_text="Whether the results of the workspace are visible to the public.",
    )

    supervisor_exclusivity_days = models.IntegerField(
        default=14,
        help_text="Number of days that a identification tasks in the queue is exclusively available to the supervisors.",
    )

    updated_at = models.DateTimeField(auto_now=True, editable=False)

    def clean(self):
        super().clean()

        if self.country and self.geom:
            country_geom = self.country.geom

            if not country_geom.covers(self.geom):
                raise ValidationError(
                    {"geom": ("Geometry must be fully inside the selected country.")}
                )

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)

    class Meta:
        constraints = [
            # country must be unique ONLY when geom is null
            models.UniqueConstraint(
                fields=["country"],
                condition=models.Q(geom__isnull=True),
                name="unique_country_when_geom_is_null",
            ),
        ]

    def __str__(self):
        country_name = "No country"
        if self.country:
            country_name = self.country.name_engl

        result = [
            country_name,
        ]
        if self.name:
            result.append(f"({self.name})")

        result.append("workspace")

        return " ".join(result)


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
        related_name="collaboration_groups_as_reviewer",
    )

    name = models.CharField(max_length=255, unique=True)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
