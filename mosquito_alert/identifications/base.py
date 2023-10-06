from django.db import models
from django.utils.translation import gettext_lazy as _


class BaseIdentifierProfile(models.Model):
    # Relations

    # Attributes - Mandatory
    is_identifier = models.BooleanField(
        default=False, help_text=_("Designates where the user can access the identification app.")
    )
    is_superidentifier = models.BooleanField(
        default=False,
        help_text=_("Designates that this user has all permissions in the identification app."),
    )
    # precision = models.FloatField(
    #    default=0.5, validators=[MinValueValidator(0), MaxValueValidator(1)]
    # )  # TODO: Keep historic of weights? Select weight according to identification updated_date

    # Attributes - Optional

    # Object Manager

    # Custom Properties
    # Methods

    # Meta and String
    class Meta:
        abstract = True
