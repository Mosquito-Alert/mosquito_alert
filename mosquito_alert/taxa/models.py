from typing import Optional

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from treebeard.mp_tree import MP_Node


class Taxon(MP_Node):
    @classmethod
    def get_root(cls) -> Optional["Taxon"]:
        return cls.get_root_nodes().first()

    @classmethod
    def get_leaves_in_rank_group(cls, rank: int) -> models.QuerySet["Taxon"]:
        rank_group = cls._convert_rank_to_rank_group(rank=rank)
        next_rank_group = rank_group + cls.RANK_GROUP_STEP
        return Taxon.objects.filter(
            rank__gte=rank_group, rank__lt=next_rank_group
        ).exclude(
            models.Exists(
                Taxon.objects.filter(
                    path__startswith=models.OuterRef("path"),
                    depth__gt=models.OuterRef("depth"),
                    rank__lt=next_rank_group,
                )
            )
        )

    @classmethod
    def _convert_rank_to_rank_group(cls, rank: int) -> int:
        # Round down to the nearest multiple of 10
        return (rank // cls.RANK_GROUP_STEP) * cls.RANK_GROUP_STEP

    class TaxonomicRank(models.IntegerChoices):
        # DOMAIN = 0, _("Domain")
        # KINGDOM = 10, _("Kingdom")
        # PHYLUM = 20, _("Phylum")
        CLASS = 30, _("Class")
        # Translators: Comes from TaxonomicRank
        ORDER = 40, _("Order")
        FAMILY = 50, _("Family")
        GENUS = 60, _("Genus")
        SUBGENUS = 61, _("Subgenus")
        SPECIES_COMPLEX = 70, _("Species complex")
        SPECIES = 71, _("Species")

    RANK_GROUP_STEP = TaxonomicRank.ORDER - TaxonomicRank.CLASS

    # Relations

    # Attributes - Mandatory
    rank = models.PositiveSmallIntegerField(choices=TaxonomicRank.choices)
    name = models.CharField(max_length=32, unique=True)
    is_relevant = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Indicates if this taxon is relevant for the application. Will be shown first and will set task to conflict if final taxon is not this.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Attributes - Optional
    common_name = models.CharField(max_length=64, null=True, blank=True)

    # Object Manager
    # Custom Properties
    node_order_by = ["name"]

    @property
    def is_specie(self):
        return self.rank >= self.TaxonomicRank.SPECIES_COMPLEX

    @property
    def italicize(self):
        return self.rank >= self.TaxonomicRank.GENUS

    @cached_property
    def parent(self) -> Optional["Taxon"]:
        return self.get_parent()

    @property
    def prev_rank_group(self) -> int:
        return self.rank_group - self.RANK_GROUP_STEP

    @property
    def next_rank_group(self) -> int:
        return self.rank_group + self.RANK_GROUP_STEP

    @property
    def rank_group(self) -> int:
        return self._convert_rank_to_rank_group(rank=self.rank)

    def get_leaves(self) -> models.QuerySet["Taxon"]:
        return self.get_descendants().filter(numchild=0)

    def get_parent_in_prev_rank_group(self) -> Optional["Taxon"]:
        return (
            self.get_ancestors()
            .filter(rank=self.prev_rank_group)
            .order_by("depth")
            .first()
        )

    def get_children_leaves_in_rank_group(self) -> models.QuerySet["Taxon"]:
        return Taxon.get_leaves_in_rank_group(rank=self.next_rank_group).filter(
            path__startswith=self.path
        )

    def get_sibling_leaves_in_rank_group(self) -> models.QuerySet["Taxon"]:
        parent_rank_group = self.get_parent_in_prev_rank_group()
        if not parent_rank_group:
            return Taxon.objects.none()

        return parent_rank_group.get_children_leaves_in_rank_group().exclude(
            path__startswith=self.path
        )

    def get_display_friendly_common_name(self) -> str:
        if self.common_name:
            return "{} ({})".format(self.common_name, self.name)

        translations_table = {  # Translators: Comes from Taxon
            112: _("species_albopictus"),
            113: _("species_aegypti"),
            114: _("species_japonicus"),
            115: _("species_koreicus"),
            10: _("species_culex"),
        }

        return translations_table.get(self.pk, _("species_other"))

    # Methods
    def clean_rank_field(self):
        if not self.parent:
            return

        if self.rank <= self.parent.rank:
            raise ValidationError(
                "Child taxon must have a higher rank than their parent."
            )

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
        if self.name:
            self.name = self.name.strip()

        if self.name and self.is_specie:
            # Capitalize only first letter
            self.name = self.name.capitalize()

        self._clean_custom_fields()

        super().save(*args, **kwargs)

    # Meta and String
    class Meta:
        db_table = "tigacrafting_taxon"  # NOTE: migrate from old tigacrafting, kept old name to avoid issues with custom third-party scripts that still uses the raw table name.
        verbose_name = _("taxon")
        verbose_name_plural = _("taxa")
        constraints = [
            models.UniqueConstraint(fields=["name", "rank"], name="unique_name_rank"),
            models.UniqueConstraint(
                fields=["depth"], condition=models.Q(depth=1), name="unique_root"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name} [{self.get_rank_display()}]"
