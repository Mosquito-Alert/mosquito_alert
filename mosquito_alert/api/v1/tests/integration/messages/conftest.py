import pytest
import uuid

from django.contrib.auth.models import User

from mosquito_alert.notifications.models import (
    Notification,
    UserSubscription,
    NotificationContent,
    NotificationRecipient,
)


# NOTE: needed for token with perms fixture
@pytest.fixture
def model_class():
    return Notification


@pytest.fixture
def user_message(user_notification):
    return user_notification


@pytest.fixture
def unseen_user_message(user_message, app_user):
    NotificationRecipient.objects.update_or_create(
        notification=user_message, user=app_user, defaults={"is_read": False}
    )

    return user_message


@pytest.fixture
def seen_user_message(user_message, app_user):
    NotificationRecipient.objects.update_or_create(
        notification=user_message, user=app_user, defaults={"is_read": True}
    )

    return user_message


@pytest.fixture
def user_message_sent_by_other_user(app_user):
    another_user = User.objects.create(username=str(uuid.uuid4()))
    notification = Notification.objects.create(
        expert=another_user,
        notification_content=NotificationContent.objects.create(
            title_en="Test title", body_html_en="Test body"
        ),
    )
    notification.send_to_user(user=app_user)

    return notification


@pytest.fixture
def topic_message(app_user, topic):
    _ = UserSubscription.objects.create(user=app_user, topic=topic)

    notification = Notification.objects.create(
        notification_content=NotificationContent.objects.create(
            title_en="Test title", body_html_en="Test body"
        )
    )
    notification.send_to_topic(topic=topic)

    return notification
