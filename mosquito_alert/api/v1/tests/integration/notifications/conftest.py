import pytest

from mosquito_alert.notifications.models import (
    Notification,
    NotificationContent,
    UserSubscription,
)


# NOTE: needed for token with perms fixture
@pytest.fixture
def model_class():
    return Notification


@pytest.fixture
def italian_user(app_user):
    app_user.locale = "it"
    app_user.save()
    return app_user


@pytest.fixture
def italian_notification(user_notification):
    user_notification.notification_content.title_native = "Titolo di prova"
    user_notification.notification_content.body_html_native = "Corpo di prova"
    user_notification.notification_content.native_locale = "it"
    user_notification.notification_content.save()
    return user_notification


@pytest.fixture
def unseen_user_notification(user_notification, app_user):
    user_notification.mark_as_unseen_for_user(user=app_user)

    return user_notification


@pytest.fixture
def seen_user_notification(user_notification, app_user):
    user_notification.mark_as_seen_for_user(user=app_user)

    return user_notification


@pytest.fixture
def report_notification(adult_report):
    notification = Notification.objects.create(
        notification_content=NotificationContent.objects.create(
            title_en="Test title", body_html_en="Test body"
        ),
        report=adult_report,
    )

    notification.send_to_user(user=adult_report.user, push=False)

    return notification


@pytest.fixture
def topic_notification(app_user, topic):
    _ = UserSubscription.objects.create(user=app_user, topic=topic)

    notification = Notification.objects.create(
        notification_content=NotificationContent.objects.create(
            title_en="Test title", body_html_en="Test body"
        )
    )
    notification.send_to_topic(topic=topic, push=False)

    return notification
