from django.db import models
from django.utils.translation import gettext_lazy as _

from mosquito_alert.individuals.models import Individual


class Bite(models.Model):
    class BodyParts(models.TextChoices):
        HEAD = "HD", _("Head")
        LEFT_ARM = "LA", _("Left arm")
        RIGHT_ARM = "RA", _("Right arm")
        CHEST = "CT", _("Chest")
        ABDOMEN = "AB", _("Abdomen")
        LEFT_LEG = "LL", _("Left leg")
        RIGHT_LEG = "RL", _("Right leg")

    # Relations
    individual = models.ForeignKey(
        Individual, null=True, blank=True, on_delete=models.PROTECT
    )

    # Attributes - Mandatory
    datetime = models.DateTimeField(auto_now_add=True)
    body_part = models.CharField(max_length=2, choices=BodyParts.choices)

    # Attributes - Optional
    # Object Manager
    # Custom Properties
    # Methods
    # Meta and String
    class Meta:
        verbose_name = _("bite")
        verbose_name_plural = _("bites")

    def __str__(self):
        return f"{self.get_body_part_display()} ({self.datetime})"
