from bs4 import BeautifulSoup
from itertools import groupby

from firebase_admin.exceptions import FirebaseError
from firebase_admin.messaging import (
    Message,
    Notification as FirebaseNotification,
    AndroidConfig,
    AndroidNotification,
    SendResponse,
)
import logging
from typing import Optional, Union

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import translation

from mosquito_alert.devices.models import Device
from mosquito_alert.notifications.managers import NotificationRecipientManager
from mosquito_alert.reports.models import Report
from mosquito_alert.users.models import TigaUser
from mosquito_alert.utils.json import DjangoGEOJSONDecoder, DjangoGEOJSONEncoder

User = get_user_model()

logger_notification = logging.getLogger("mosquitoalert.notification")


class NotificationContent(models.Model):
    title = models.TextField()
    body_html = models.TextField()

    def get_title(self, language_code: str) -> str:
        with translation.override(language_code):
            return self.title

    def get_body_html(self, language_code: str) -> str:
        with translation.override(language_code):
            return self.body_html

    def get_body(self, language_code: str) -> str:
        body_html = self.get_body_html(language_code=language_code)
        soup = BeautifulSoup(body_html, "html.parser")
        body = soup.find("body")  # Try to find the <body> tag
        if body:
            return body.get_text(
                separator=" ", strip=True
            )  # If <body> is found, extract text
        else:
            # If no <body> tag is found, return text from the entire HTML document
            return soup.get_text(separator=" ", strip=True)

    def get_body_image(self, language_code: str) -> Optional[str]:
        soup = BeautifulSoup(
            self.get_body_html(language_code=language_code),
            "html.parser",
        )

        img_tag = soup.find("img")
        if img_tag:
            return img_tag.get("src")

        return None

    class Meta:
        # NOTE: migrate from old tigaserver_app, kept old name to avoid issues with custom third-party scripts that still uses the raw table name.
        db_table = "tigaserver_app_notificationcontent"


class Notification(models.Model):
    class Target(models.TextChoices):
        USERS = "users", "Users"
        AUDIENCE = "audience", "Audience"

    report = models.ForeignKey(
        Report,
        null=True,
        blank=True,
        related_name="report_notifications",
        help_text="Report regarding the current notification",
        on_delete=models.CASCADE,
    )
    recipients = models.ManyToManyField(
        TigaUser, through="NotificationRecipient", related_name="notifications"
    )
    expert = models.ForeignKey(
        User,
        null=True,
        blank=True,
        related_name="expert_notifications",
        help_text="Expert sending the notification",
        on_delete=models.SET_NULL,
    )
    audience = models.JSONField(
        null=True,
        blank=True,
        encoder=DjangoGEOJSONEncoder,
        decoder=DjangoGEOJSONDecoder,
        help_text="Criteria used to select recipients. It is the audience filter for the notification, in django ORM filter format",
    )
    date_comment = models.DateTimeField(auto_now_add=True)
    # blank is True to avoid problems in the migration, this should be removed!!
    notification_content = models.ForeignKey(
        NotificationContent,
        related_name="notification_content",
        help_text="Multi language content of the notification",
        on_delete=models.PROTECT,
    )

    @property
    def target(self) -> Target.choices:
        if self.audience is not None:
            return self.Target.AUDIENCE
        else:
            return self.Target.USERS

    def get_fcm_message(self, language_code: str) -> Message:
        # See: https://firebase.google.com/docs/reference/admin/python/firebase_admin.messaging
        # See: https://firebaseopensource.com/projects/flutter/plugins/packages/firebase_messaging/readme/
        return Message(
            data={"id": str(self.pk)},
            notification=FirebaseNotification(
                title=self.notification_content.get_title(language_code=language_code),
                body=self.notification_content.get_body(language_code=language_code),
                image=self.notification_content.get_body_image(
                    language_code=language_code
                ),
            ),
            android=AndroidConfig(
                notification=AndroidNotification(
                    click_action="FLUTTER_NOTIFICATION_CLICK"
                ),
                # NOTE: priority high is needed to show notification when the app is in foreground.
                # see https://firebase.google.com/docs/cloud-messaging/flutter/receive#foreground_and_notification_messages
                priority="high",
            ),
        )

    # TODO: Should this be async (celery task)
    def send_to_user(self, user: TigaUser) -> None:
        NotificationRecipient.objects.get_or_create(user=user, notification=self)

    def _send_to_audience(self) -> None:
        if self.audience is None:
            return

        recipients_qs = TigaUser.objects.filter(**self.audience)
        # NOTE: groupby requires the queryset to be ordered by the key function, so we order by locale.
        for locale, user_group in groupby(
            recipients_qs.order_by("locale").iterator(), key=lambda x: x.locale
        ):
            NotificationRecipient.objects.bulk_create(
                [
                    NotificationRecipient(notification=self, user=user)
                    for user in user_group
                ],
                batch_size=2000,
                ignore_conflicts=True,
            )
            Device.objects.filter(user__in=user_group).send_message(
                message=self.get_fcm_message(language_code=locale)
            )

    def save(self, *args, **kwargs):
        is_adding = self._state.adding

        super().save(*args, **kwargs)

        if is_adding:
            try:
                # TODO: If there is a geometry filter, check that the geometry is valid
                self._send_to_audience()
            except Exception:
                pass

    class Meta:
        # NOTE: migrate from old tigaserver_app, kept old name to avoid issues with custom third-party scripts that still uses the raw table name.
        db_table = "tigaserver_app_notification"
        permissions = [
            (
                "bypass_audience_scope",
                "Can bypass audience scope",
            ),
        ]


class NotificationRecipient(models.Model):
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE)
    user = models.ForeignKey(TigaUser, on_delete=models.CASCADE)

    is_read = models.BooleanField(default=False)

    objects = NotificationRecipientManager()

    # TODO: Make it async (celery task)
    def send_push(self) -> Union[SendResponse, None]:

        if settings.DISABLE_PUSH:
            return

        message = self.notification.get_fcm_message(
            language_code=self.user.locale or "en"
        )

        try:
            return self.user.devices.all().send_message(message=message).response
        except (FirebaseError, ValueError) as e:
            logger_notification.exception(str(e))
        except Exception as e:
            logger_notification.exception(str(e))

    def save(self, *args, **kwargs):
        is_adding = self._state.adding

        super().save(*args, **kwargs)

        if is_adding:
            try:
                self.send_push()
            except Exception:
                pass

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["notification", "user"],
                name="unique_notification_recipient",
            )
        ]
