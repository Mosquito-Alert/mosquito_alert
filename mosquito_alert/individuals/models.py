from __future__ import annotations

import typing

from django.db import models
from django.utils.translation import gettext_lazy as _

from mosquito_alert.images.models import Photo
from mosquito_alert.taxa.models import Taxon

from .managers import IndividualManager

if typing.TYPE_CHECKING:
    from mosquito_alert.identifications.models import IndividualIdentificationTaskResult


class Individual(models.Model):
    @classmethod
    def _get_default_identification_result_type(cls):
        from mosquito_alert.identifications.models import BaseTaskResult

        return BaseTaskResult.ResultType.ENSEMBLED

    # Relations

    # Attributes - Mandatory

    # Attributes - Optional
    # Object Manager
    objects = IndividualManager()

    # Custom Properties
    @property
    def default_identification_result(self) -> IndividualIdentificationTaskResult | None:
        return self.get_identification_result_by_type(type=self._get_default_identification_result_type())

    @property
    def is_identified(self) -> bool:
        return self.taxon is not None and self.taxon.is_specie

    @property
    def taxon(self) -> Taxon | None:
        return self.default_identification_result.taxon if self.default_identification_result else None

    @property
    def photos(self) -> models.QuerySet[Photo]:
        return self.get_photos_by_identification_result_type(type=self._get_default_identification_result_type())

    # Methods
    def get_photos_by_identification_result_type(self, type) -> models.QuerySet[Photo]:
        return Photo.objects.filter(
            photo_identification_tasks__task=self.identification_task,
            photo_identification_tasks__results__type=type,
        )

    def get_identification_result_by_type(self, type) -> IndividualIdentificationTaskResult | None:
        return self.identification_task.results.filter(type=type).first()

    # Meta and String
    class Meta:
        verbose_name = _("individual")
        verbose_name_plural = _("individuals")

    def __str__(self) -> str:
        return str(self.taxon) if self.taxon else f"Not-identified individual (id={self.pk})"
