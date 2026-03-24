
from django.db.models.signals import post_save
from django.dispatch import receiver

from mosquito_alert.tigaserver_app.models import Report

from .models import NotificationTopic, UserSubscription


@receiver(post_save, sender=Report)
def subscribe_user_to_country_topic(sender, instance, created, **kwargs):
    if not created:
        return

    topic_code_candidates = [instance.country, instance.nuts_2, instance.nuts_3]
    for topic_code in filter(lambda x: x is not None, topic_code_candidates):
        try:
            topic = NotificationTopic.objects.get(topic_code=topic_code)
        except NotificationTopic.DoesNotExist:
            pass
        else:
            UserSubscription.objects.get_or_create(
                user=instance.user,
                topic=topic
            )
