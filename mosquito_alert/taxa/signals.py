# from django.db.models.signals import m2m_changed
# from django.dispatch import receiver

# from mosquito_alert.geo.models import Location
from mosquito_alert.individuals.models import Individual

from .models import SpecieDistribution

# from mosquito_alert.individuals.models import post_identification_changed


# @receiver(post_identification_changed, sender=Individual)
def update_distribution_on_identification_change(instance: Individual, *args, **kwargs):
    if hasattr(instance, "reports"):
        for r in instance.reports.all():
            for b in r.location.boundaries.all():
                # By default, status is computed automatically on create.
                obj, created = SpecieDistribution.objects.get_or_create(
                    boundary=b,
                    taxon=instance.taxon,
                    month=r.observed_at,
                )
                if not created:
                    # Update status
                    obj.recompute_status(commit=True)


# @receiver(m2m_changed, sender=Location.boundaries.through)
def update_distribution_on_location_boundaries_changed(instance, action, pk_set, reverse, *args, **kwargs):
    if action in ["post_add", "post_remove", "post_clear"]:
        boundaries_ids = pk_set
        if reverse:
            boundaries_ids = [instance]

        md_to_update_qs = SpecieDistribution.objects.filter(boundary__in=boundaries_ids)
        for md_to_update in md_to_update_qs:
            md_to_update.recompute_status(commit=True)
