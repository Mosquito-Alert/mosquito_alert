from bs4 import BeautifulSoup
from collections import Counter
from firebase_admin.exceptions import FirebaseError
from firebase_admin.messaging import (
    Message,
    Notification as FirebaseNotification,
    AndroidConfig,
    AndroidNotification,
    SendResponse,
    BatchResponse,
)
import logging
from typing import Optional, Union

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models

from mosquito_alert.devices.models import Device
from mosquito_alert.reports.models import Report
from mosquito_alert.users.models import TigaUser

User = get_user_model()

logger_notification = logging.getLogger("mosquitoalert.notification")


class NotificationContent(models.Model):
    body_html_es = models.TextField(
        default=None,
        blank=True,
        null=True,
        help_text="Expert comment, expanded and allows html, in spanish",
    )
    body_html_ca = models.TextField(
        default=None,
        blank=True,
        null=True,
        help_text="Expert comment, expanded and allows html, in catalan",
    )
    body_html_en = models.TextField(
        default=None,
        blank=True,
        null=True,
        help_text="Expert comment, expanded and allows html, in english",
    )
    title_es = models.TextField(
        default=None,
        blank=True,
        null=True,
        help_text="Title of the comment, shown in non-detail view, in spanish",
    )
    title_ca = models.TextField(
        default=None,
        blank=True,
        null=True,
        help_text="Title of the comment, shown in non-detail view, in catalan",
    )
    title_en = models.TextField(
        default=None,
        blank=True,
        null=True,
        help_text="Title of the comment, shown in non-detail view, in english",
    )
    predefined_available_to = models.ForeignKey(
        User,
        blank=True,
        null=True,
        related_name="predefined_notifications",
        help_text="If this field is not null, this notification is predefined - the predefined map notifications will go here. This field indicates the expert to which the notification is available",
        on_delete=models.SET_NULL,
    )
    body_html_native = models.TextField(
        default=None,
        blank=True,
        null=True,
        help_text="Expert comment, expanded and allows html, in the language indicated by the field native_locale",
    )
    title_native = models.TextField(
        default=None,
        blank=True,
        null=True,
        help_text="Title of the comment, shown in non-detail view, in the language indicated by the field title_native",
    )
    native_locale = models.CharField(
        default=None,
        blank=True,
        null=True,
        max_length=10,
        help_text="Locale code for text in body_html_native and title_native",
    )
    notification_label = models.CharField(
        default=None,
        blank=True,
        null=True,
        max_length=255,
        help_text="Arbitrary label used to group thematically equal notifications. Optional. ",
    )

    def _get_localized_field(
        self,
        fieldname_prefix: str,
        language_code: Optional[str] = None,
        fallback: bool = True,
    ) -> str:
        # Default to english
        language_code = language_code or "en"

        if (
            self.native_locale
            and self.native_locale.lower().strip() == language_code.lower().strip()
        ):
            language_code = "native"

        # Check if the field for the specified language exists
        result_en = getattr(self, f"{fieldname_prefix}_en")
        result_local = None
        fieldname = f"{fieldname_prefix}_{language_code}"
        if hasattr(self, fieldname):
            result_local = getattr(self, fieldname)

        # Return result with fallback to English
        if fallback:
            return result_local or result_en or ""
        return result_local or ""

    def get_title(
        self, language_code: Optional[str] = None, fallback: bool = True
    ) -> str:
        return self._get_localized_field(
            fieldname_prefix="title", language_code=language_code, fallback=fallback
        )

    def get_body_html(
        self, language_code: Optional[str] = None, fallback: bool = True
    ) -> str:
        return self._get_localized_field(
            fieldname_prefix="body_html", language_code=language_code, fallback=fallback
        )

    def get_body(
        self, language_code: Optional[str] = None, fallback: bool = True
    ) -> str:
        body_html = self.get_body_html(language_code=language_code, fallback=fallback)
        soup = BeautifulSoup(body_html, "html.parser")
        body = soup.find("body")  # Try to find the <body> tag
        if body:
            return body.get_text(
                separator=" ", strip=True
            )  # If <body> is found, extract text
        else:
            # If no <body> tag is found, return text from the entire HTML document
            return soup.get_text(separator=" ", strip=True)

    def get_body_image(
        self, language_code: Optional[str] = None, fallback: bool = True
    ) -> Optional[str]:
        soup = BeautifulSoup(
            self.get_body_html(language_code=language_code, fallback=fallback),
            "html.parser",
        )

        img_tag = soup.find("img")
        if img_tag:
            return img_tag.get("src")

        return None

    def save(self, *args, **kwargs):
        if not (self.title_native and self.body_html_native):
            self.native_locale = None
        super().save(*args, **kwargs)

    class Meta:
        db_table = "tigaserver_app_notificationcontent"  # NOTE: migrate from old tigaserver_app, kept old name to avoid issues with custom third-party scripts that still uses the raw table name.


class Notification(models.Model):
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
    date_comment = models.DateTimeField(auto_now_add=True)
    # blank is True to avoid problems in the migration, this should be removed!!
    notification_content = models.ForeignKey(
        NotificationContent,
        related_name="notification_content",
        help_text="Multi language content of the notification",
        on_delete=models.PROTECT,
    )

    def get_fcm_message(self, language_code: str) -> Message:
        # See: https://firebase.google.com/docs/reference/admin/python/firebase_admin.messaging
        # See: https://firebaseopensource.com/projects/flutter/plugins/packages/firebase_messaging/readme/
        return Message(
            data={"id": str(self.notification.pk)},
            notification=FirebaseNotification(
                title=self.notification.notification_content.get_title(
                    language_code=language_code
                ),
                body=self.notification.notification_content.get_body(
                    language_code=language_code
                ),
                image=self.notification.notification_content.get_body_image(
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

    def send_to_topic(self, topic: "NotificationTopic") -> None:
        topic.send_notification(notification=self)

    def send_to_user(self, user: TigaUser) -> None:
        NotificationRecipient.objects.get_or_create(user=user, notification=self)

    class Meta:
        db_table = "tigaserver_app_notification"  # NOTE: migrate from old tigaserver_app, kept old name to avoid issues with custom third-party scripts that still uses the raw table name.


class NotificationRecipient(models.Model):
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE)
    user = models.ForeignKey(TigaUser, on_delete=models.CASCADE)

    through_topics = models.ManyToManyField("NotificationTopic", blank=True)

    is_read = models.BooleanField(default=False)

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


TOPIC_GROUPS = (
    (0, "General"),
    (1, "Language topics"),
    (2, "Country topics"),
    (3, "Country nuts3"),
    (4, "Country nuts2"),
    (5, "Special"),
)


class NotificationTopic(models.Model):
    topic_code = models.CharField(
        max_length=100, unique=True, help_text="Code for the topic."
    )
    topic_description = models.TextField(
        help_text="Description for the topic, in english."
    )
    topic_group = models.IntegerField(
        "Group of topics",
        choices=TOPIC_GROUPS,
        default=0,
        help_text="Your degree of belief that at least one photo shows a tiger mosquito breeding site",
    )

    def send_notification(
        self, notification: Notification
    ) -> Union[BatchResponse, None]:
        bulk_recipients = []
        users = []
        users_qs = TigaUser.objects.filter(user_subscriptions__topic=self)
        for user in users_qs.iterator():
            users.append(user)
            bulk_recipients.append(
                NotificationRecipient(notification=notification, user=user)
            )

        if len(users) == 0:
            return

        _ = NotificationRecipient.objects.bulk_create(
            bulk_recipients, batch_size=1000, ignore_conflicts=True
        )
        # NOTE: ignore_conflicts make returned object not having its pk set.
        for recipient in NotificationRecipient.objects.filter(
            user__in=users
        ).iterator():
            recipient.through_topics.add(self)

        if settings.DISABLE_PUSH:
            return

        majority_locale = Counter(u.locale for u in users).most_common(1)[0][0]
        return Device.send_topic_message(
            message=self.notification.get_fcm_message(language_code=majority_locale),
            topic_name=self.sent_to_topic.topic_code,
        )

    class Meta:
        db_table = "tigaserver_app_notificationtopic"  # NOTE: migrate from old tigaserver_app, kept old name to avoid issues with custom third-party scripts that still uses the raw table name.


class UserSubscription(models.Model):
    user = models.ForeignKey(
        TigaUser,
        related_name="user_subscriptions",
        help_text="User which is subscribed to the topic",
        on_delete=models.CASCADE,
    )
    topic = models.ForeignKey(
        NotificationTopic,
        related_name="topic_users",
        help_text="Topics to which the user is subscribed",
        on_delete=models.CASCADE,
    )

    def save(self, *args, **kwargs):
        if self._state.adding:
            try:
                self.user.devices.all().handle_topic_subscription(
                    should_subscribe=True,  # Subscribe
                    topic=self.topic.topic_code,
                )
            except ValueError as e:
                logger_notification.exception(str(e))

        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        try:
            self.user.devices.all().handle_topic_subscription(
                should_subscribe=False,  # Unsubscribe
                topic=self.topic.topic_code,
            )
        except ValueError as e:
            logger_notification.exception(str(e))

        return super().delete(*args, **kwargs)

    class Meta:
        db_table = "tigaserver_app_usersubscription"  # NOTE: migrate from old tigaserver_app, kept old name to avoid issues with custom third-party scripts that still uses the raw table name.
        unique_together = (
            "user",
            "topic",
        )
