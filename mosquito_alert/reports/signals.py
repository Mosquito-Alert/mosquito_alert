from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from mosquito_alert.identifications.models import (
    BaseTaskResult,
    IndividualIdentificationTask,
    IndividualIdentificationTaskResult,
    PhotoIdentificationTask,
    classification_has_changed,
    identification_task_has_changed,
)
from mosquito_alert.notifications.signals import notify, notify_subscribers
from mosquito_alert.reports.models import IndividualReport


# TODO: improve + add tests
@receiver(identification_task_has_changed, sender=IndividualIdentificationTask)
def notify_new_individual_identified_in_report(sender, instance, fields_changed, **kwargs):
    if not instance.is_completed:
        return

    result = instance.results.filter(type=BaseTaskResult.ResultType.ENSEMBLED).first()
    if not result:
        return

    taxon = result.taxon
    for r in instance.individual.reports.all():
        if user := r.user:
            # Notify the user that has sent the report.
            notify.send(
                recipient=user,
                sender=r,
                verb=_("has new individual identified as"),
                action_object=taxon,
                description=_(f"An individual has been identified in your observation report as {taxon}"),
            )
            for b in r.location.boundaries.all():
                notify_subscribers.send(
                    sender=taxon,
                    verb=_("was identified in"),
                    target=b,
                )

    notify_subscribers.send(
        sender=taxon,
        verb=_("was identified"),
    )


@receiver(classification_has_changed, sender=IndividualIdentificationTaskResult)
def notify_individual_identified_in_report(sender, instance, fields_changed, **kwargs):
    # If notify on delete -> skip
    if not instance.pk:
        return

    TRIGGER_FIELDS = ["label"]
    # If label or probability have not changed -> skip
    if not any([x in fields_changed for x in TRIGGER_FIELDS]):
        return

    # If label is not specie and probability
    # if not instance.label.is_specie:
    #    return

    # Only consider ENSEMLBED result
    if not instance.type == BaseTaskResult.ResultType.ENSEMBLED:
        return

    if not instance.task.is_completed:
        return

    for r in instance.task.individual.reports.all():
        if user := r.user:
            # Notify the user that has sent the report.
            notify.send(
                recipient=user,
                sender=r,
                verb=_("has new individual identified as"),
                action_object=instance.taxon,
                description=_(f"An individual has been identified in your observation report as {instance.taxon}"),
            )
            for b in r.location.boundaries.all():
                notify_subscribers.send(
                    sender=instance.taxon,
                    verb=_("was identified in"),
                    target=b,
                )

    notify_subscribers.send(
        sender=instance.taxon,
        verb=_("was identified"),
    )


@receiver(post_save, sender=PhotoIdentificationTask)
def add_new_individual_to_report(sender, instance: PhotoIdentificationTask, created, **kwargs):
    if not created:
        return

    new_individual = instance.task.individual

    for r in (
        IndividualReport.objects.filter(photos__in=[instance.photo]).exclude(individuals__in=[new_individual]).all()
    ):
        r.individuals.add(new_individual)


@receiver(post_delete, sender=PhotoIdentificationTask)
def update_report_individuals_m2m(sender, instance, **kwargs):
    individual = instance.task.individual
    individual_photos = individual.photos.all()

    for r in IndividualReport.objects.exclude(photos__in=individual_photos).filter(individuals__in=[individual]).all():
        r.individuals.remove(individual)
