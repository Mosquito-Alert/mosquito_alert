from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.mail import send_mail
from django.db.models.query import QuerySet
from django.db.models.signals import post_save
from django.dispatch import Signal, receiver
from notifications.models import notify_handler as _notify_handler
from notifications.signals import notify  # noqa: F401

from .models import Notification, NotificationSubscription

User_model = get_user_model()


notify_subscribers = Signal()


@receiver(notify_subscribers)
def event_handler(sender, **kwargs):
    """
    Handler function to manage notifications depending on user subscriptions
    """

    # Get users subscribed to this actor.
    users_pk_to_notify = list(
        NotificationSubscription.objects.for_actor(obj=sender)
        .for_target(obj=kwargs.get("target", None), allow_null=True)
        .values_list("user", flat=True)
        .distinct()
    )
    users_subscribed_qs = User_model.objects.filter(pk__in=users_pk_to_notify)

    if recipient := kwargs.get("recipient"):

        if isinstance(recipient, Group):
            recipient = recipient.user_set.all()

        if isinstance(recipient, QuerySet) and recipient.model is User_model:
            # Keep only those users that are subscribed to this target.
            users_subscribed_qs = users_subscribed_qs.intersection(recipient)
        elif isinstance(recipient, (list, User_model)):
            # Cast to list if not iterable
            try:
                iter(recipient)
            except TypeError:
                recipient = list(recipient)

            users_subscribed_qs = users_subscribed_qs.filter(
                pk__in=[r.pk for r in recipient if isinstance(r, User_model)]
            )

    _notify_handler(sender=sender, recipient=users_subscribed_qs, **kwargs)


@receiver(post_save, sender=Notification)
def send_notification_email(instance, created, *args, **kwargs):
    # TODO: send mail async + django-anymail
    if created:
        if isinstance(instance.recipient, User_model) and (
            email := instance.recipient.email
        ):
            message = instance.description
            is_sent = send_mail(
                subject=str(instance),
                message=message,
                recipient_list=[email],
                fail_silently=True,
                from_email=None,  # Will use settings.DEFAULT_FROM_EMAIL
            )
            instance.emailed = bool(is_sent)
            instance.save()
