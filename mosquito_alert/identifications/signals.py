import random

from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver

from mosquito_alert.annotations.models import BaseShape
from mosquito_alert.individuals.models import Individual
from mosquito_alert.reports.models import IndividualReport
from mosquito_alert.taxa.models import Taxon

from .models import (
    BaseClassification,
    IndividualIdentificationTask,
    PhotoIdentificationTask,
    Prediction,
    TaxonClassificationCandidate,
)


@receiver(post_save, sender=Individual)
def create_identification_task_on_individual_creation(sender, instance, created, **kwargs):
    if created:
        _ = IndividualIdentificationTask.objects.create(individual=instance)


# TODO: remove. only for testing purposes
@receiver(m2m_changed, sender=IndividualReport.photos.through)
def create_dummy_prediction(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action != "post_add":
        return

    # Dummy prediction that detects same individual on all images
    sex = random.choice(BaseClassification.SexOptions.values)
    label = Taxon.objects.filter(rank__gte=Taxon.TaxonomicRank.GENUS).order_by("?").first()
    shape_type = BaseShape.ShapeType.RECTANGLE

    individual = Individual.objects.create()
    for p in model.objects.filter(pk__in=pk_set):
        photo_task = PhotoIdentificationTask.objects.create(photo=p, task=individual.identification_task)
        probability = random.uniform(0.6, 1.0)
        shape_points = [
            [
                random.uniform(0, 0.5),
                random.uniform(0, 0.5),
            ],
            [
                random.uniform(0.5, 1),
                random.uniform(0.5, 1),
            ],
        ]
        p = Prediction.objects.create(
            task=photo_task, sex=sex, shape_type=shape_type, points=shape_points, skip_notify_changes=True
        )
        _ = TaxonClassificationCandidate.objects.create(
            label=label, probability=probability, is_seed=True, content_object=p
        )
        p.skip_notify_changes = False
        p.recompute_candidates_tree()
