from django.db.models.signals import post_save
from django.dispatch import receiver

from mosquito_alert.geo.models import Country

from .models import Workspace


@receiver(post_save, sender=Country)
def create_workspace_for_country(sender, instance: Country, created: bool, **kwargs):
    """Create a workspace for the country of a report when an identification task is created."""
    if created:
        Workspace.objects.create(country=instance)
