

from django.test import TestCase

from mosquito_alert.tigaserver_app.models import NotificationTopic, UserSubscription
from mosquito_alert.users.models import TigaUser


class TigaUserModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.global_topic = NotificationTopic.objects.create(topic_code='global')

    def test_create_new_user_subscribe_to_global_topic(self):
        tiga_user = TigaUser.objects.create()

        subscription_to_global_topic = UserSubscription.objects.filter(
            user=tiga_user,
            topic=self.global_topic
        )

        self.assertTrue(subscription_to_global_topic.exists())

    def test_create_new_user_subscribe_to_locale_topic(self):
        locale = 'es'
        spanish_topic = NotificationTopic.objects.create(topic_code=locale)
        tiga_user = TigaUser.objects.create(locale=locale)

        subscription_to_spanish_topic = UserSubscription.objects.filter(
            user=tiga_user,
            topic=spanish_topic
        )

        self.assertTrue(subscription_to_spanish_topic.exists())

    def test_create_new_with_non_existing_notification_topic_locale_do_not_raise(self):
        locale = 'es'

        # Ensure Notification topic for locale does not exist
        NotificationTopic.objects.filter(topic_code=locale).delete()

        _ = TigaUser.objects.create(locale=locale)
