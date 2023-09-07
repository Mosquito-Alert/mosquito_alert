from django.db import models
from django.db.models.query import QuerySet

from .querysets import IndividualQuerySet


class BaseIndividualManager(models.Manager):
    def get_queryset(self) -> QuerySet:
        return super().get_queryset().select_related("identification_task")


IndividualManager = BaseIndividualManager.from_queryset(IndividualQuerySet)
