from django.db.models import Manager

from .querysets import NotificationSubscriptionQuerySet

NotificationSubscriptionManager = Manager.from_queryset(
    NotificationSubscriptionQuerySet
)
