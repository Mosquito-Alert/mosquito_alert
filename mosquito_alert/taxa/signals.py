from django.dispatch import receiver

# from mosquito_alert.geo.models import Location
from mosquito_alert.identifications.models import (
    BaseTaskResult,
    IndividualIdentificationTaskResult,
    classification_has_changed,
)

from .models import SpecieDistribution


# TODO: test signals
@receiver(classification_has_changed, sender=IndividualIdentificationTaskResult)
def update_distribution_on_identification_change(sender, instance, *args, **kwargs):
    if not instance.task.is_completed:
        return

    # Only consider ENSEMLBED result
    if not instance.type == BaseTaskResult.ResultType.ENSEMBLED:
        return

    for r in instance.task.individual.reports.all():
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
