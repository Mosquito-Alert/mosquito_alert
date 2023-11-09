from django.db.models import Subquery
from django.dispatch import receiver

from mosquito_alert.geo.models import Boundary
from mosquito_alert.identifications.models import (
    BaseTaskResult,
    IndividualIdentificationTaskResult,
    classification_has_changed,
)

from .models import SpecieDistribution


# TODO: trigger on individual taxon change.
@receiver(classification_has_changed, sender=IndividualIdentificationTaskResult)
def update_distribution_on_identification_change(sender, instance, *args, **kwargs):
    # TODO: run for previous taxon (before change) and current taxon and recompute distribution for both.
    if not instance.task.is_completed:
        return

    # Only consider ENSEMLBED result
    if not instance.type == BaseTaskResult.ResultType.ENSEMBLED:
        return

    if not instance.taxon.is_specie:
        return

    reports_qs = instance.task.individual.reports.browsable()

    first_reported_datetime = None
    if reports_qs.exists():
        first_reported_datetime = reports_qs.order_by("observed_at").first().observed_at

    for b in Boundary.objects.filter(numchild=0, locations__in=Subquery(reports_qs.values("location__pk"))).distinct():
        # By default, status is computed automatically on create.
        SpecieDistribution.update_for(boundary=b, taxon=instance.taxon, from_datetime=first_reported_datetime)


# @receiver(m2m_changed, sender=Location.boundaries.through)
def update_distribution_on_location_boundaries_changed(instance, action, pk_set, reverse, *args, **kwargs):
    if action in ["post_add", "post_remove", "post_clear"]:
        boundaries_ids = pk_set
        if reverse:
            boundaries_ids = [instance]

        md_to_update_qs = SpecieDistribution.objects.filter(boundary__in=boundaries_ids)
        for md_to_update in md_to_update_qs:
            md_to_update.recompute_status(commit=True)
