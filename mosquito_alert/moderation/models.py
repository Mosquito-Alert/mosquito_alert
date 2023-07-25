from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from flag.models import Flag

from .managers import FlagModeratedManager


class FlagModeratedModel(models.Model):
    IS_BANNED_STATES = (Flag.State.FLAGGED.value, Flag.State.NOTIFIED.value)

    # Relations
    # NOTE: the field name should be flags
    flags = GenericRelation(Flag)

    # Attributes - Mandatory
    # Attributes - Optional

    # Object Manager
    objects = FlagModeratedManager()

    # Custom Properties
    @property
    def is_permitted(self):
        return not self.is_banned

    @property
    def is_banned(self):
        if flags := self.flags.all():
            states = flags.values_list("state", flat=True)
            # Return if any state of flags is in banned states
            return not set(states).isdisjoint(self.IS_BANNED_STATES)
        else:
            return False

    # Methods

    # Meta and String
    class Meta:
        abstract = True
