from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.db.models.signals import ModelSignal
from django.utils.translation import gettext_lazy as _
from django_lifecycle import AFTER_CREATE, AFTER_UPDATE, BEFORE_UPDATE, LifecycleModel, hook
from treebeard.mp_tree import MP_Node

from mosquito_alert.geo.models import Boundary
from mosquito_alert.notifications.models import Notification
from mosquito_alert.notifications.signals import notify_subscribers
from mosquito_alert.utils.fields import ProxyAwareHistoricalRecords
from mosquito_alert.utils.models import ParentManageableNodeMixin, TimeStampedModel

distribution_status_has_changed = ModelSignal()

# Interesting data sources:
#     * http://itis.gov
#     * https://www.catalogueoflife.org | https://github.com/CatalogueOfLife/coldp#taxon
#     * (alternatives) https://www.ncbi.nlm.nih.gov/taxonomy


class Taxon(ParentManageableNodeMixin, TimeStampedModel, MP_Node):
    @classmethod
    def get_root(cls) -> Taxon | None:
        return cls.get_root_nodes().first()

    class TaxonomicRank(models.IntegerChoices):
        DOMAIN = 0, _("Domain")
        KINGDOM = 10, _("Kingdom")
        PHYLUM = 20, _("Phylum")
        CLASS = 30, _("Class")
        # Translators: Comes from TaxonomicRank
        ORDER = 40, _("Order")
        FAMILY = 50, _("Family")
        GENUS = 60, _("Genus")
        SUBGENUS = 61, _("Subgenus")
        SPECIES_COMPLEX = 70, _("Species complex")
        SPECIES = 71, _("Species")

    # Relations

    # Attributes - Mandatory
    rank = models.PositiveSmallIntegerField(choices=TaxonomicRank.choices)
    name = models.CharField(max_length=32)

    # Attributes - Optional
    common_name = models.CharField(max_length=64, null=True, blank=True)
    gbif_id = models.PositiveBigIntegerField(null=True, blank=True)

    # Object Manager
    # Custom Properties
    node_order_by = ["name"]  # Needed for django-treebeard

    @property
    def gbif_url(self) -> str:
        if self.gbif_id:
            return f"https://www.gbif.org/species/{self.gbif_id}"

        return ""

    @property
    def is_specie(self):
        return self.rank >= self.TaxonomicRank.SPECIES_COMPLEX

    # Methods
    def clean_rank_field(self):
        if not self.parent:
            return

        if self.rank <= self.parent.rank:
            raise ValidationError("Child taxon must have a higher rank than their parent.")

    def _clean_custom_fields(self, exclude=None) -> None:
        if exclude is None:
            exclude = []

        errors = {}
        if "rank" not in exclude:
            try:
                self.clean_rank_field()
            except ValidationError as e:
                errors["rank"] = e.error_list

        if errors:
            raise ValidationError(errors)

    def clean_fields(self, exclude=None) -> None:
        super().clean_fields(exclude=exclude)
        self._clean_custom_fields(exclude=exclude)

    def save(self, *args, **kwargs):
        if self.name and self.is_specie:
            # Capitalize only first letter
            self.name = self.name.capitalize()

        self._clean_custom_fields()

        super().save(*args, **kwargs)

    # Meta and String
    class Meta(TimeStampedModel.Meta):
        verbose_name = _("taxon")
        verbose_name_plural = _("taxa")
        constraints = TimeStampedModel.Meta.constraints + [
            models.UniqueConstraint(fields=["name", "rank"], name="unique_name_rank"),
            models.UniqueConstraint(fields=["depth"], condition=Q(depth=1), name="unique_root"),
        ]

    def __str__(self) -> str:
        return f"{self.name} [{self.get_rank_display()}]"


class SpecieDistribution(LifecycleModel, TimeStampedModel):
    class DataSource(models.TextChoices):
        SELF = "self", "Mosquito Alert"
        ECDC = "ecdc", _("European Centre for Disease Prevention and Control")

    class DistributionStatus(models.TextChoices):
        ABSENT = "abs", _("Absent")
        REPORTED = "rep", _("Reported")
        INTRODUCED = "int", _("Introduced")
        ESTABLISHED = "est", _("Established")

    # Relations
    boundary = models.ForeignKey(Boundary, on_delete=models.PROTECT, related_name="+")
    taxon = models.ForeignKey(
        Taxon,
        limit_choices_to={"rank__gte": Taxon.TaxonomicRank.SPECIES_COMPLEX},
        on_delete=models.PROTECT,
        related_name="distribution",
    )

    # Attributes - Mandatory
    source = models.CharField(max_length=8, choices=DataSource.choices)
    status = models.CharField(max_length=3, choices=DistributionStatus.choices)

    # Attributes - Optional

    # Object Manager
    # Custom Properties
    history = ProxyAwareHistoricalRecords(
        inherit=True,
        cascade_delete_history=True,
        excluded_fields=("boundary", "taxon", "source", "created_at", "updated_at"),  # Tracking status only
    )

    # Methods
    @hook(AFTER_CREATE)
    @hook(AFTER_UPDATE, when="status", has_changed=True)
    def notify_status_change(self):
        # TODO: Change it, raise an alert.
        notify_subscribers.send(
            sender=self.taxon,
            verb="had its status updated to",
            target=self.boundary,
            level=Notification.LEVELS.warning,
            status=self.status,
        )

    @hook(AFTER_CREATE)
    @hook(AFTER_UPDATE, when="status", has_changed=True)
    def send_distributation_status_changed_signal(self):
        # TODO: Remove: Use alert.
        distribution_status_has_changed.send(
            sender=self.__class__,
            instance=self,
            prev_status=self.initial_value(field_name="status"),
        )

    # TODO: Ask how to aggregate
    # @hook(AFTER_UPDATE, when="status", has_changed=True)
    def update_relatives_on_status_change(self):
        # Update by boundary parent (same taxon)
        common_qs = self.__class__.objects.filter(
            status__lt=self.status,  # Only update if status is less than current.
            month__gte=self.month,  # Only update date from this month onwards.
        )
        for future_distribution in common_qs.filter(taxon=self.taxon, boundary=self.boundary):
            future_distribution.status = self.status
            future_distribution.save()

        if b_parent := self.boundary.parent:
            ancestors_b_qs = common_qs.filter(taxon=self.taxon, boundary=b_parent, source=self.source)
            for ancestor_b in ancestors_b_qs:
                ancestor_b.status = self.status
                ancestor_b.save()

    @hook(BEFORE_UPDATE, when="status", has_changed=False)
    def _disable_history_record(self):
        # See: django-simple-history docu
        self.skip_history_when_saving = True

    def save(self, *args, **kwargs):
        if hasattr(self, "taxon") and not self.taxon.is_specie:
            raise ValueError("Taxon must be species rank.")

        try:
            super().save(*args, **kwargs)
        finally:
            if hasattr(self, "skip_history_when_saving"):
                del self.skip_history_when_saving

    # Meta and String
    class Meta(TimeStampedModel.Meta):
        verbose_name = _("specie distribution")
        verbose_name_plural = _("species distribution")
        constraints = TimeStampedModel.Meta.constraints + [
            models.UniqueConstraint(fields=["boundary", "taxon", "source"], name="unique_boundary_taxon_source"),
        ]

    def __str__(self) -> str:
        # See: https://github.com/jazzband/django-simple-history/issues/533
        #      https://github.com/jazzband/django-simple-history/issues/521
        # return f"[{self.get_source_display()}]: {self.get_status_display()}"
        return super().__str__()
