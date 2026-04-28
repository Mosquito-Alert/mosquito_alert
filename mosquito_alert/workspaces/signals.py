from django.db.models.signals import post_save
from django.dispatch import receiver

from mosquito_alert.geo.models import EuropeCountry

from .models import Workspace


@receiver(post_save, sender=EuropeCountry)
def create_workspace_for_new_country(sender, instance, created, **kwargs):
    if not created:
        return

    Workspace.objects.create(country=instance)
