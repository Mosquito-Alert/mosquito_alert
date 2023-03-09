from django.db import models
from django.db.models import Count, Max, Q, Sum
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


class Taxon(ParentManageableNodeMixin, MP_Node):
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

    @property
    def is_specie(self):
        return self.rank >= self.TaxonomicRank.SPECIES_COMPLEX

    # Methods
    def save(self, *args, **kwargs):
        if self.name:
            # Capitalize only first letter
            self.name = self.name.capitalize()

        if self.parent:
            print(f"parent {self} is {self.parent}")
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
            models.UniqueConstraint(fields=["name", "rank"], name="unique_name_rank"),
            models.UniqueConstraint(
                fields=["depth"], condition=Q(depth=1), name="unique_root"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name} [{self.get_rank_display()}]"


class MonthlyDistribution(LifecycleModel):
    """The manner in which a biological taxon is spatially arranged."""

    # TODO: duplicate previous month rows on first day of the month.

    class DistributionStatus(models.IntegerChoices):
        # NOTE: write in ascending status order!
        ABSENT = 0, _("Absent")
        INTRODUCED = 10, _("Introduced")
        ESTABLISHED = 20, _("Established")

    # Relations
    # TODO: use unique_for_month instead of constraint?
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
    def send_distributation_status_changed_signal(self):
        distribution_status_has_changed.send(
            sender=self.__class__,
            instance=self,
            prev_status=self.initial_value(field_name="status"),
        )

    @hook(AFTER_UPDATE, when="status", has_changed=True)
    def update_relatives_on_status_change(self):
        # Update by boundary parent (same taxon)
        common_qs = self.__class__.objects.filter(
            status__lt=self.status,  # Only update if status is less than current.
            month__gte=self.month,  # Only update date from this month onwards.
        )
        for future_distribution in common_qs.filter(
            taxon=self.taxon, boundary=self.boundary
        ):
            future_distribution.status = self.status
            future_distribution.save()

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

    def _get_inherited_status(self):

        # If any taxon/boundary descendant is found, use its status.
        qs = self.__class__.objects.filter(month__lte=self.month)

        q_boundary = Q(boundary=self.boundary)
        if b_descendants := self.boundary.get_descendants():
            q_boundary = q_boundary | Q(boundary__in=b_descendants)
        qs = qs.filter(q_boundary)

        q_taxon = Q(taxon=self.taxon)
        if t_descendants := self.taxon.get_descendants():
            q_taxon = q_taxon | Q(taxon__in=t_descendants)
        qs = qs.filter(q_taxon)

        if self.pk:
            qs = qs.exclude(pk=self.pk)

        result = (
            qs.annotate(max_status=Max("status"))
            .values("month", "max_status")
            .order_by("month")
            .last()
        )

        return result

    def recompute_status(self, commit=True):
        # NOTE: placing import here to avoid circular import
        from mosquito_alert.reports.models import IndividualReport

        # TODO: Make new rules. Only for demo purposes.
        # Getting the IndividualReports of interest:
        #     * Report observation date previous than self.month
        #     * Report location is self.boundary (or descendat)
        #     * Individal has been marked as indentified
        #     * The taxon assigned to individual is self.taxon
        report_qs = (
            IndividualReport.objects.filter(
                observed_at__month__lte=self.month.month,
                observed_at__year__lte=self.month.year,
                individual__taxon__isnull=False,
            )
            .filter(
                Q(individual__taxon=self.taxon)
                | Q(individual__taxon__in=self.taxon.get_descendants())
            )
            .filter_by_boundary(boundaries=self.boundary, include_descendants=True)
        )
        num_results = report_qs.annotate(
            num_of_individual=Count("individual")
        ).aggregate(total_individuals=Sum("num_of_individual", default=0))[
            "total_individuals"
        ]

        result = self.DistributionStatus.ABSENT
        if num_results > 0:
            result = self.DistributionStatus.INTRODUCED
        elif num_results > 5:
            result = self.DistributionStatus.ESTABLISHED

        if self.status is None or result > self.status:
            self.status = result
            if commit:
                self.save()

    def save(self, *args, **kwargs) -> None:

        if self.status is None:
            self.recompute_status(commit=False)

        if self._state.adding:
            # Create new for boundary parent (same taxon)
            if b_parent := self.boundary.parent:
                _ = self.__class__.objects.update_or_create(
                    taxon=self.taxon,
                    boundary=b_parent,
                    month=self.month,
                    defaults=dict(
                        status=self.status,
                    ),
                )

            # Create new for taxon parent (same boundary)
            if t_parent := self.taxon.parent:
                _ = self.__class__.objects.update_or_create(
                    taxon=t_parent,
                    boundary=self.boundary,
                    month=self.month,
                    defaults=dict(
                        status=self.status,
                    ),
                )

        if self.has_changed("status"):
            affected_instances_qs = self.__class__.objects.filter(
                month__gte=self.month,
                status__gt=self.status,
            ).filter(
                Q(boundary__in=self.boundary.get_children())
                | Q(boundary=self.boundary)
                | Q(taxon__in=self.taxon.get_children())
                | Q(taxon=self.taxon)
            )

            if affected_instances_qs.count():
                raise ValueError(
                    f"Can not change {self.boundary} status to {self.get_status_display()}."
                    "It is lower than any of its relatives' status."
                )

        # TODO: discuss if a status can go backward.
        #       If True, needs to check when adding new status.
        # Getting previous month's status
        # previous_status = self.__class__.objects.filter(
        #     boundary=self.boundary,
        #     taxon=self.taxon,
        #     month=self.month - 1
        # ).values_list('status', flat=True).first()

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
