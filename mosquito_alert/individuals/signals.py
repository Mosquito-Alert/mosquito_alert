from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from mosquito_alert.reports.models import IndividualReport


@receiver(m2m_changed, sender=IndividualReport.photos.through)
def sync_individual_photos_with_reported(sender, instance, action, pk_set, **kwargs):
    if action == "post_add":
        instance.individual.photos.add(*pk_set)
    elif action == "post_remove":
        instance.individual.photos.remove(*pk_set)
