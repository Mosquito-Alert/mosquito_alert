from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from mosquito_alert.geo.models import Boundary
from mosquito_alert.utils.models import TimeStampedModel


class BoundaryAuthorization(TimeStampedModel):
    # Relations
    boundary = models.OneToOneField(Boundary, on_delete=models.CASCADE, related_name="authorization")
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, through="BoundaryMembership")

    # Attributes - Mandatory
    supervisor_exclusivity_days = models.PositiveSmallIntegerField(default=15)
    members_only = models.BooleanField(default=False)

    # Attributes - Optional

    # Object Manager
    # Custom Properties
    # Methods
    # Meta and String
    class Meta(TimeStampedModel.Meta):
        verbose_name = _("Boundary Authorization")
        verbose_name_plural = _("Boundary Authorizations")


class BoundaryMembership(TimeStampedModel):
    class RoleType(models.TextChoices):
        SUPERVISOR = "s", _("Supervisor")
        IDENTIFICATOR = "i", _("Identificator")
        VIEWER = "v", _("Viewer")

    # Relations
    boundary_authorization = models.ForeignKey(
        BoundaryAuthorization, on_delete=models.CASCADE, related_name="memberships"
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="boundary_memberships")

    # Attributes - Mandatory
    role = models.CharField(max_length=1, choices=RoleType.choices, db_index=True)

    # Attributes - Optional

    # Object Manager
    # Custom Properties
    # Methods
    # Meta and String
    class Meta(TimeStampedModel.Meta):
        pass
