from django.db import models

from .querysets import BaseIdentificationQuerySet, TaxonClassificationCandidateQuerySet, UserIdentificationQuerySet


class BaseTaxonAnnotationManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("label")


TaxonClassificationCandidateManager = BaseTaxonAnnotationManager.from_queryset(TaxonClassificationCandidateQuerySet)

BasePhotoIdentificationManager = models.Manager.from_queryset(BaseIdentificationQuerySet)
UserIdentificationManager = BasePhotoIdentificationManager.from_queryset(UserIdentificationQuerySet)
