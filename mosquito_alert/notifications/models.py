from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _
from notifications.base.models import AbstractNotification
from notifications.signals import notify

from .managers import NotificationSubscriptionManager


class Notification(AbstractNotification):
    class Meta(AbstractNotification.Meta):
        abstract = False


class NotificationSubscription(models.Model):
    # Relations
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_index=True,
        related_name="notification_subscriptions",
    )

    actor_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        db_index=True,
        related_name="notification_subscription_as_actor",
    )
    actor_object_id = models.CharField(
        max_length=255,
        db_index=True,
    )  # Using CharField for UUID cases
    subscribed_actor = GenericForeignKey("actor_content_type", "actor_object_id")

    target_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        db_index=True,
        null=True,
        blank=True,
        related_name="notification_subscription_as_target",
    )
    target_object_id = models.CharField(
        max_length=255, db_index=True, null=True, blank=True
    )  # Using CharField for UUID cases
    subscribed_target = GenericForeignKey("target_content_type", "target_object_id")

    # Attributes - Mandatory
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    # Attributes - Optional
    level = models.CharField(choices=Notification.LEVELS, max_length=20, null=True, blank=True)

    # Object Manager
    objects = NotificationSubscriptionManager()

    # Custom Properties
    # Methods
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        notify.send(
            sender=self.user,
            recipient=self.user,
            verb="has subscribed to",
            action_object=self.subscribed_actor,
            target=self.subscribed_target,
        )

    # Meta and String
    class Meta:
        verbose_name = _("notification subscription")
        verbose_name_plural = _("notification subscription")
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "user",
                    "actor_content_type",
                    "actor_object_id",
                    "target_content_type",
                    "target_object_id",
                    "level",
                ],
                name="unique_user_notification_subscription",
            )
        ]

    def __str__(self):
        msg = f"{self.user} -> {self.subscribed_actor}"
        if self.subscribed_target:
            msg += f" in {self.subscribed_target}"
        return msg
