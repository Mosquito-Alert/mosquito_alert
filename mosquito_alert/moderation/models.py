import uuid

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from mosquito_alert.utils.models import TimeStampedModel, update_object_counter

from .managers import FlagInstanceManager, FlagManager, FlagModeratedManager

# NOTE: only working with models whose pk is UUID.
#       Beware on which model you use it.
# See: https://code.djangoproject.com/ticket/16055


class Flag(TimeStampedModel):
    """Used to add flag/moderation to a model"""

    # Relations
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey("content_type", "object_id")

    moderator = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="flags_moderated"
    )

    # Attributes - Mandatory
    is_active = models.BooleanField(default=False)
    count = models.PositiveIntegerField(default=0, editable=False)

    # Attributes - Optional
    moderated_at = models.DateTimeField(null=True, blank=True, editable=False)

    # Object Manager
    objects = FlagManager()

    # Custom Properties
    @property
    def has_been_reviewed(self) -> bool:
        return self.moderated_at is not None

    # Methods
    def increase_count(self) -> None:
        update_object_counter(obj=self, fieldname="count", inc_value=1)

        # If already moderated and is not active, but people still adding
        # tags, force pending moderation.
        if self.has_been_reviewed and not self.is_active:
            self.moderated_at = None
            self.moderator = None
            self.save(update_fields=["moderated_at", "moderator"])

    def decrease_count(self) -> None:
        update_object_counter(obj=self, fieldname="count", inc_value=-1)

    # Meta and String
    class Meta(TimeStampedModel.Meta):
        verbose_name = _("Flag")
        verbose_name_plural = _("Flags")
        constraints = TimeStampedModel.Meta.constraints + [
            models.UniqueConstraint(
                fields=["content_type", "object_id"],
                name="unique_by_content_object",
            )
        ]


class FlagInstance(TimeStampedModel):
    class Reason(models.IntegerChoices):
        SPAM = 1, _("Spam | Exists only to promote a service")
        ABUSIVE = 2, _("Abusive | Intended at promoting hatred")
        OTHER = 100, _("Something else.")

    # Relations
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_flags",
    )
    flag = models.ForeignKey(Flag, on_delete=models.CASCADE, related_name="flags")

    # Attributes - Mandatory
    reason = models.PositiveSmallIntegerField(choices=Reason.choices)

    # Attributes - Optional
    notes = models.TextField(null=True, blank=True)

    # Object Manager
    objects = FlagInstanceManager()

    # Custom Properties
    # Methods
    def clean(self) -> None:
        """If something else is choosen, notes shall not be empty"""
        if self.reason == self.Reason.OTHER and not self.notes:
            raise ValidationError(
                {
                    "notes": ValidationError(
                        _("Please provide some information why you choose to report the content"), code="required"
                    )
                }
            )

    def save(self, *args, **kwargs) -> None:
        self.clean()

        is_adding = self._state.adding

        super().save(*args, **kwargs)

        if is_adding:
            self.flag.increase_count()

    def delete(self, *args, **kwargs):
        _result = super().delete(*args, **kwargs)

        self.flag.decrease_count()

        return _result

    # Meta and String
    class Meta(TimeStampedModel.Meta):
        verbose_name = _("Flag Instance")
        verbose_name_plural = _("Flag Instances")
        constraints = TimeStampedModel.Meta.constraints + [
            models.UniqueConstraint(
                fields=["flag", "user"],
                name="unique_flag_by_user",
            )
        ]


class FlagModeratedModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relations
    flags = GenericRelation(Flag)

    # Attributes - Mandatory
    # Attributes - Optional

    # Object Manager
    objects = FlagModeratedManager()

    # Custom Properties
    @property
    def is_flagged(self) -> bool:
        return self.flags.filter(is_active=True).exists()

    # Methods

    # Meta and String
    class Meta:
        abstract = True
