from django.db import models
from django.db.models import Max, Q
from django.db.models.signals import ModelSignal
from django.utils.translation import gettext_lazy as _
from django_lifecycle import AFTER_UPDATE, LifecycleModel, hook
from month.models import MonthField
from treebeard.mp_tree import MP_Node

from mosquito_alert.geo.models import Boundary
from mosquito_alert.notifications.models import Notification
from mosquito_alert.notifications.signals import notify_subscribers

from ..utils.models import ParentManageableNodeMixin

distribution_status_has_changed = ModelSignal()

# Interesting data sources:
#     * http://itis.gov
#     * https://www.catalogueoflife.org | https://github.com/CatalogueOfLife/coldp#taxon
#     * (alternatives) https://www.ncbi.nlm.nih.gov/taxonomy


class Taxon(MP_Node, ParentManageableNodeMixin):
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
    created_at = models.DateTimeField(auto_now_add=True)

    # Attributes - Optional
    common_name = models.CharField(max_length=64, null=True, blank=True)

    # Object Manager
    # Custom Properties
    node_order_by = ["name"]  # Needed for django-treebeard

    # Methods
    def save(self, *args, **kwargs):
        # Forcing capital letters
        self.name = self.name.title()

        if self.parent:
            if self.rank <= self.parent.rank:
                raise ValueError(
                    "Child taxon must have a higher rank than their parent."
                )

        super().save(*args, **kwargs)

    # Meta and String
    class Meta:
        verbose_name = _("taxon")
        verbose_name_plural = _("taxa")
        constraints = [
            models.UniqueConstraint(fields=["name", "rank"], name="unique_name_rank")
        ]

    def __str__(self) -> str:
        return f"{self.name} [{self.get_rank_display()}]"


class MonthlyDistribution(LifecycleModel):
    """The manner in which a biological taxon is spatially arranged."""

    # TODO: duplicate previous month rows on first day of the month.
    # TODO: add signal -> Location boundary m2m change (only for IndividualReports).
    #                     On indivudal, identifiaction change.

    class DistributionStatus(models.IntegerChoices):
        # NOTE: write in ascending status order!
        ABSENT = 0, _("Absent")
        INTRODUCED = 10, _("Introduced")
        ESTABLISHED = 20, _("Established")

    @classmethod
    def _get_inherited_status(cls, instance):

        # If any taxon/boundary descendant is found, use its status.
        qs = cls.objects.filter(month__lte=instance.month)

        q_boundary = Q(boundary=instance.boundary)
        if b_descendants := instance.boundary.get_descendants():
            q_boundary = q_boundary | Q(boundary__in=b_descendants)
        qs = qs.filter(q_boundary)

        q_taxon = Q(taxon=instance.taxon)
        if t_descendants := instance.taxon.get_descendants():
            q_taxon = q_taxon | Q(taxon__in=t_descendants)
        qs = qs.filter(q_taxon)

        if instance.pk:
            qs = qs.exclude(pk=instance.pk)

        result = (
            qs.annotate(max_status=Max("status"))
            .values("month", "max_status")
            .order_by("month")
            .last()
        )

        return result

    @classmethod
    def _get_recomputed_status(cls, instance):
        # NOTE: placing import here to avoid circular import
        from mosquito_alert.reports.models import IndividualReport

        # TODO: Make new rules. Only for demo purposes.
        # TODO: take into account previous month status.

        report_qs = IndividualReport.objects.filter(
            observed_at__month__lte=instance.month.month,
            observed_at__year__lte=instance.month.year,
            location__boundaries=instance.boundary,
            individual__is_identified=True,
            individual__identification_set__taxon=instance.taxon,
        )
        num_results = report_qs.count()

        result = instance.status
        if num_results > 0:
            result = cls.DistributionStatus.INTRODUCED
        elif num_results > 5:
            result = cls.DistributionStatus.ESTABLISHED

        return result if result > instance.status else instance.status

    @classmethod
    def recompute_multiple_status(cls, taxon, month, boundary=None):
        filter_kwargs = dict(taxon=taxon, month=month)

        if boundary:
            filter_kwargs["boundary"] = boundary

        for obj_update in cls.objects.filter(**filter_kwargs).all():
            new_status = obj_update._get_recomputed_status()
            if new_status != obj_update.status:
                obj_update.status = new_status
                obj_update.save()

    # Relations
    boundary = models.ForeignKey(
        Boundary, on_delete=models.CASCADE, related_name="distribution"
    )
    taxon = models.ForeignKey(
        Taxon, on_delete=models.CASCADE, related_name="distribution"
    )

    # Attributes - Mandatory
    # TODO: add periodicity? It will let have monthly, weekly in same table
    status = models.PositiveSmallIntegerField(choices=DistributionStatus.choices)
    month = MonthField()
    # TODO: add data-source?

    # Attributes - Optional
    # Object Manager
    # Custom Properties
    # Methods
    @hook(AFTER_UPDATE, when="status", has_changed=True)
    def notify_status_change(self):
        notify_subscribers.send(
            sender=self.taxon,
            verb="had its status updated to",
            target=self.boundary,
            level=Notification.LEVELS.warning,
            status=self.status,
        )

    @hook(AFTER_UPDATE, when="status", has_changed=True)
    def update_relatives_on_status_change(self):
        distribution_status_has_changed.send(
            sender=self.__class__,
            instance=self,
            prev_status=self.initial_value(field_name="status"),
        )

        # Update by boundary parent (same taxon)
        common_qs = self.__class__.objects.filter(
            status__lt=self.status,  # Only update if status is less than current.
            month__gte=self.month,  # Only update date from this month onwards.
        )
        if b_parent := self.boundary.parent:
            ancestors_b_qs = common_qs.filter(
                taxon=self.taxon,
                boundary=b_parent,
            )
            for ancestor_b in ancestors_b_qs:
                ancestor_b.status = self.status
                ancestor_b.save()

        # Update by taxon parent (same boundary)
        if t_parent := self.taxon.parent:
            ancestors_t_qs = common_qs.filter(
                taxon=t_parent,
                boundary=self.boundary,
            )
            for ancestor_t in ancestors_t_qs:
                ancestor_t.status = self.status
                ancestor_t.save()

    def save(self, *args, **kwargs) -> None:

        if not self.status:
            self.status = self._get_inherited_status()

        # TODO: discuss if a status can go backward.
        #       If True, needs to check when adding new status.

        super().save(*args, **kwargs)

    # Meta and String
    class Meta:
        verbose_name = _("monthly distribution")
        verbose_name_plural = _("monthly distributions")
        constraints = [
            models.UniqueConstraint(
                fields=["boundary", "taxon", "month"],
                name="unique_taxon_boundary_month",
            )
        ]

    def __str__(self) -> str:
        return f"[{self.boundary}] {self.taxon} ({self.month}): {self.get_status_display()}"
