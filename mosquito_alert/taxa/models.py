from __future__ import annotations

import itertools
from datetime import datetime

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Count, F, Max, Min, Q, Subquery, Window
from django.db.models.functions import DenseRank, Now, RowNumber
from django.db.models.signals import ModelSignal
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_jsonform.models.fields import JSONField
from django_lifecycle import AFTER_CREATE, AFTER_UPDATE, BEFORE_CREATE, BEFORE_UPDATE, LifecycleModel, hook
from treebeard.mp_tree import MP_Node

from mosquito_alert.geo.models import Boundary
from mosquito_alert.notifications.models import Notification
from mosquito_alert.notifications.signals import notify_subscribers
from mosquito_alert.utils.fields import ProxyAwareHistoricalRecords
from mosquito_alert.utils.models import ParentManageableNodeMixin, TimeStampedModel

from .managers import SpecieDistributionManager

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
    gbif_id = models.PositiveBigIntegerField(null=True, blank=True, unique=True)

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
        SELF = "self", "Mosquito Alert"  # NOTE: all status are automatically computed. Can not force status.
        ECDC = "ecdc", _("European Centre for Disease Prevention and Control")

    class DistributionStatus(models.IntegerChoices):
        # Sorted from best to worst case scenario. Will be used on aggregations.
        ABSENT = 0, _("Absent")  # At the moment only used for ECDC
        REPORTED = 10, _("Reported")
        INTRODUCED = 20, _("Introduced")
        ESTABLISHED = 30, _("Established")

    # NOTE: Check format in playground on any change:
    # https://bhch.github.io/react-json-form/playground/
    STATS_SUMMARY_SCHEMA = {
        "type": "object",
        "title": _("Statistics summary by status"),
        "keys": {status_key: {"$ref": "#/$defs/statistics"} for status_key in DistributionStatus.values},
        "$defs": {
            "statistics": {
                "type": "oybject",
                "required": "true",
                "keys": {
                    "percentage": {"type": "number", "required": "true", "minimum": 0, "maximum": 100},
                    "count": {"type": "integer", "required": "true", "minimum": 0},
                },
            }
        },
    }

    @classmethod
    def update_for(cls, boundary: Boundary, taxon: Taxon, from_datetime: datetime | None = None) -> None:
        boundary_leafs = Boundary.get_tree(parent=boundary).filter(numchild=0)
        taxon_leafs = Taxon.get_tree(parent=taxon).filter(numchild=0)

        for b_leaf, t_leaf in itertools.product(boundary_leafs, taxon_leafs):
            obj, created = SpecieDistribution.objects.get_or_create(
                boundary=b_leaf, taxon=t_leaf, source=cls.DataSource.SELF
            )
            if not created:
                obj.update(from_datetime=from_datetime)

    # Relations
    boundary = models.ForeignKey(
        Boundary, limit_choices_to={"numchild": 0}, on_delete=models.PROTECT, related_name="+"
    )
    taxon = models.ForeignKey(
        Taxon,
        limit_choices_to={"rank__gte": Taxon.TaxonomicRank.SPECIES_COMPLEX},
        on_delete=models.PROTECT,
        related_name="distribution",
    )

    # Attributes - Mandatory
    source = models.CharField(max_length=8, choices=DataSource.choices)
    status_since = models.DateTimeField(default=timezone.now, blank=True, editable=False)

    # Attributes - Optional
    status = models.PositiveSmallIntegerField(
        choices=DistributionStatus.choices,
        null=True,
        blank=True,
    )
    stats_summary = JSONField(schema=STATS_SUMMARY_SCHEMA, null=True, blank=True, editable=False)

    # Object Manager
    objects = SpecieDistributionManager()

    # Custom Properties
    history = ProxyAwareHistoricalRecords(
        inherit=True,
        cascade_delete_history=True,
        excluded_fields=(
            "boundary",
            "taxon",
            "source",
            "created_at",
            "updated_at",
            "status_since",
        ),  # Tracking status and stats_summary only
    )

    @property
    def is_source_self(self) -> bool:
        return self.source == self.DataSource.SELF

    @property
    def pretty_stats_summary(self) -> dict:
        result = {}
        for key, value in self.stats_summary.items():
            try:
                result[SpecieDistribution.DistributionStatus(int(key)).label] = value
            except ValueError:
                result[key] = value

        return result

    # Methods
    @staticmethod
    def _apply_datetime_filters(
        changes: list[tuple[datetime, object]],
        from_datetime: datetime | None = None,
        to_datetime: datetime | None = None,
    ) -> list[tuple[datetime, object]]:
        """
        Apply datetime filters.

        :param changes: List of status changes.
        :param from_datetime: Start datetime for filtering changes.
        :param to_datetime: End datetime for filtering changes.
        :return: List of filtered status changes.
        """
        if from_datetime:
            changes = filter(lambda x: x[0] >= from_datetime, changes)
        if to_datetime:
            changes = filter(lambda x: x[0] <= to_datetime, changes)
        return sorted(list(changes), key=lambda x: x[0]) if changes else []

    def _get_status_changes_from_reports(
        self, from_datetime: datetime | None = None, to_datetime: datetime | None = None
    ) -> list[tuple[datetime, DistributionStatus] | None]:
        from mosquito_alert.reports.models import IndividualReport

        report_count_stats_qs = (
            IndividualReport.objects.browsable()
            .filter_by_boundary(boundaries=[self.boundary], include_descendants=True)
            .with_identified_taxon(taxon=self.taxon, include_descendants=True)
            .annotate(
                datetime=F("observed_at"),
                cumcount=Window(expression=RowNumber(), order_by=F("observed_at").asc()),
                num_consecutive_years=Window(expression=DenseRank(), order_by="observed_at__year") - 1,
            )
            .values("datetime", "cumcount", "num_consecutive_years")
            .order_by("datetime")
        )

        # Status triggers:
        #     - ESTABLISHED:    if reports found in two different years.
        #     - INTRODUCED:     first time reached 4 reports in the same year.
        #     - REPORTED:       first report detected ever.
        #     - ABSENT:         # TODO: if sampling_effort but no reports found
        # NOTE: order is important. First filter the last status possible.
        result = []
        # NOTE: using python functions from now on for filtering, so only 1 query is sent to DB.
        report_count_stats = list(report_count_stats_qs)
        for filter_kwargs, status in (
            (dict(num_consecutive_years=1), self.DistributionStatus.ESTABLISHED),
            (dict(cumcount=4), self.DistributionStatus.INTRODUCED),
            (dict(cumcount=1), self.DistributionStatus.REPORTED),
        ):
            if _first_occurence := next(
                filter(lambda x: all(x[key] == value for key, value in filter_kwargs.items()), report_count_stats),
                None,
            ):
                result.append((_first_occurence["datetime"], status))

                # From now on, this is the upper limit to have a lower rank status.
                report_count_stats = list(
                    filter(lambda x: x["datetime"] < _first_occurence["datetime"], report_count_stats)
                )

        return self._apply_datetime_filters(changes=result, from_datetime=from_datetime, to_datetime=to_datetime)

    def _get_status_changes_from_children(
        self, from_datetime: datetime | None = None, to_datetime: datetime | None = None
    ) -> list[tuple[datetime, DistributionStatus] | None]:
        children_qs = (
            SpecieDistribution.history.exclude(status__isnull=True)
            .filter(
                id__in=Subquery(
                    SpecieDistribution.objects.get_children_for_instance(
                        instance=self, include_taxon_descendants=True
                    ).values("pk")
                )
            )
            .annotate(datetime=F("history_date"))
        )

        children_status_qs = (
            children_qs.annotate(max_status=Window(expression=Max("status"), order_by=F("datetime").asc()))
            .values("datetime", "max_status")
            .order_by("datetime")
        )

        result = []
        for _element in children_status_qs.all().iterator():
            status = SpecieDistribution.DistributionStatus(_element["max_status"])
            if not len(result) or result[-1][-1] != status:
                # Only if the last element of the last result is not status, add
                # So we allow to fluctuate over time, but not repetitions.
                result.append((_element["datetime"], status))

        return self._apply_datetime_filters(changes=result, from_datetime=from_datetime, to_datetime=to_datetime)

    def get_status_changes(
        self, from_datetime: datetime | None = None, to_datetime: datetime | None = None
    ) -> list[tuple[datetime, DistributionStatus] | None]:
        if not self.is_source_self:
            return []

        if self.boundary.is_leaf():
            # Case is leaf: recompute counting individual reports
            result = self._get_status_changes_from_reports(from_datetime=from_datetime, to_datetime=to_datetime)
        else:
            # Case is not leaf: aggregate from children boundaries.
            result = self._get_status_changes_from_children(from_datetime=from_datetime, to_datetime=to_datetime)

        return result

    def get_stats_summary_changes(
        self, to_datetime: datetime | None = None, from_datetime: datetime | None = None
    ) -> list[tuple[datetime, dict] | None]:
        if not self.is_source_self:
            return []

        # Return if is leaf.
        if self.boundary.is_leaf():
            return []

        leaf_status_qs = SpecieDistribution.history.exclude(status__isnull=True).filter(
            id__in=Subquery(
                SpecieDistribution.objects.get_leaves_for_instance(
                    instance=self,
                    include_taxon_descendants=False,  # Only boundary leafs not to break percentage computations.
                ).values("pk")
            )
        )

        leaf_status_change_qs = (
            leaf_status_qs.values("id")
            .annotate(datetime=Min("history_date"))
            .values("id", "datetime", "status")
            .order_by("datetime")
        )

        if from_datetime:
            leaf_status_change_qs = leaf_status_change_qs.filter(datetime__gte=from_datetime)

        if to_datetime:
            leaf_status_change_qs = leaf_status_change_qs.filter(datetime__lte=to_datetime)

        # Set default result to all stats to 0 for each status.
        default_status_result = {
            status_key: {"percentage": 0, "count": 0} for status_key in self.DistributionStatus.values
        }

        # Get number of boundary leafs (will be used for the percentages)
        total_leafs = self.boundary.get_descendants().filter(numchild=0).count()

        # Building the result
        result = []
        # For each date found in the queryset
        for _current_datetime in leaf_status_change_qs.values_list("datetime", flat=True).distinct():
            count_by_status = (
                leaf_status_qs.filter(history_date__lte=_current_datetime)
                .latest_of_each()
                .as_instances()
                .values("status")
                .annotate(count=Count(1))
                .values("status", "count")
            )
            count_by_status_dict = {
                x["status"]: {"percentage": 100 * x["count"] / total_leafs, "count": x["count"]}
                for x in count_by_status
            }

            # Case leafs without data
            _num_none_leafs = total_leafs - sum(
                value["count"] for value in count_by_status_dict.values() if "count" in value
            )
            count_by_status_dict["None"] = {
                "percentage": 100 * _num_none_leafs / total_leafs,
                "count": _num_none_leafs,
            }

            result.append((_current_datetime, default_status_result | count_by_status_dict))

        return sorted(result, key=lambda x: x[0]) if result else []

    @transaction.atomic
    def _rebuild_history(
        self,
        status_changes: list[tuple[datetime, DistributionStatus] | None],
        stats_summary_changes: list[tuple[datetime, dict] | None],
        from_datetime: datetime | None = None,
    ) -> None:
        first_change_datetime = min([x[0] for x in status_changes + stats_summary_changes], default=None)

        # Checking that from_datetime is not greater thant the first change datetime.
        if all([from_datetime, first_change_datetime]) and from_datetime > first_change_datetime:
            raise ValueError(
                f"'from_datetime' ({from_datetime}) must be less than the first change date ({first_change_datetime})."
            )

        # Select the history candidates to be deleted at the end if not updated.
        history_to_delete_qs = self.history
        if from_datetime:
            history_to_delete_qs = history_to_delete_qs.filter(history_date__gte=from_datetime)

        # Get the most recent values (if exist)
        try:
            _last_valid_instance = (
                self.history.as_of(date=from_datetime)  # NOTE: can raise self.DoesNotExist
                if from_datetime
                else self.history.as_instances().earliest(
                    "history_date"
                )  # NOTE: can raise self.history.model.DoesNotExist
            )
            last_status = _last_valid_instance.status
            last_stats_summary = _last_valid_instance.stats_summary
        except (self.DoesNotExist, self.history.model.DoesNotExist):
            last_status = self.status if from_datetime and from_datetime >= self.status_since else None
            last_stats_summary = (
                self.stats_summary
                if all([from_datetime, self.updated_at]) and from_datetime >= self.updated_at
                else None
            )

        exclude_history_to_delete = []
        for date_time in sorted({x[0] for x in status_changes + stats_summary_changes}):
            # Find the most recent datetime in array status_changes
            last_status = next(
                (
                    status
                    for dt, status in sorted(status_changes, key=lambda x: abs(x[0] - date_time))
                    if date_time >= dt
                ),
                last_status,
            )
            # Find the most recent datetime in array stats_summary_changes
            last_stats_summary = next(
                (
                    price
                    for dt, price in sorted(stats_summary_changes, key=lambda x: abs(x[0] - date_time))
                    if date_time >= dt
                ),
                last_stats_summary,
            )

            # Create new history record
            obj, _ = self.history.model.objects.update_or_create(
                id=self.pk,
                history_date=date_time,
                defaults=dict(status=last_status, stats_summary=last_stats_summary, history_type="~"),
            )
            exclude_history_to_delete.append(obj.pk)

        # Proceed to delete
        _ = history_to_delete_qs.exclude(pk__in=exclude_history_to_delete).delete()

        # Ensure only 1 created history type exists and it's the first one.
        first_history_record = self.history.order_by("history_date").first()
        if first_history_record:
            first_history_record.history_type = "+"
            first_history_record.save(update_fields=["history_type"])
        else:
            # Create
            first_history_record = self.history.model.objects.create(
                id=self.pk,
                history_type="+",
                history_date=self.status_since,
                status=self.status,
                stats_summary=self.stats_summary,
            )

        # Set all history record that are not the first one type to "UPDATE".
        self.history.exclude(pk=first_history_record.pk).update(history_type="~")

        # Ensure last history record contains current values
        # last_history_record = self.history.order_by("history_date").last()
        # last_history_record.status = self.status
        # last_history_record.stats_summary = self.stats_summary
        # last_history_record.save(update_fields=["status", "stats_summary"])

    @hook(BEFORE_CREATE)
    @transaction.atomic
    def update(self, from_datetime: datetime | None = None) -> None:
        status_changes = self.get_status_changes()
        stats_summary_changes = self.get_stats_summary_changes()

        # Setting current values
        if status_changes:
            self.status = status_changes[-1][-1]
            self.status_since = status_changes[-1][0]
        else:
            # NOTE: status_since is auto computed.
            self.status = None

        self.stats_summary = stats_summary_changes[-1][-1] if stats_summary_changes else None

        # Only if object is already created. This only when called by BEFORE_CREATE hook.
        if self.pk:
            self.skip_history_when_saving = True
            self.save()

            # Rebuild history if object exist
            self._rebuild_history(
                status_changes=self._apply_datetime_filters(changes=status_changes, from_datetime=from_datetime),
                stats_summary_changes=self._apply_datetime_filters(
                    changes=stats_summary_changes, from_datetime=from_datetime
                ),
                from_datetime=from_datetime,
            )

    @hook(AFTER_CREATE)
    @hook(AFTER_UPDATE, when="status", has_changed=True)
    def notify_status_change(self):
        if not self.is_source_self:
            return
        # TODO: Change it, raise an alert.
        notify_subscribers.send(
            sender=self.taxon,
            verb=f"had its status updated (valid from {self.status_since}) to",
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

    @hook(AFTER_CREATE)
    @hook(AFTER_UPDATE, when="status", has_changed=True)
    def update_parents(self) -> None:
        if not self.is_source_self:
            return

        # Save all qs kwargs for all parent combinations
        parents_qs_kwargs = []

        # Same boundary but with parent taxon (only specie)
        # NOTE: important to first query by taxon and after boundary.
        if t_parent := self.taxon.parent:
            if t_parent.is_specie:
                parents_qs_kwargs.append(dict(boundary=self.boundary, taxon=t_parent, source=self.source))

        # Same taxon but with parent boundary
        if b_parent := self.boundary.parent:
            parents_qs_kwargs.append(dict(boundary=b_parent, taxon=self.taxon, source=self.source))

        for parent_qs_kwargs in parents_qs_kwargs:
            # NOTE: on create: status and stats are automatically computed. See AFTER_CREATE hooks.
            obj, created = SpecieDistribution.objects.get_or_create(**parent_qs_kwargs)
            if not created:
                obj.update()

    @hook(BEFORE_UPDATE, when="status", has_changed=True)
    def _update_status_since(self):
        if not self.has_changed("status_since"):
            self.status_since = timezone.now()

    def save(self, *args, **kwargs) -> None:
        if hasattr(self, "taxon") and not self.taxon.is_specie:
            raise ValueError("Taxon must be species rank.")

        # Only save history record when any of "status" or "stats_summary" has changed.
        # Otherwise it always crate a new record. See: https://github.com/jazzband/django-simple-history/issues/287
        is_adding = self._state.adding
        if not is_adding and not any(map(lambda x: self.has_changed(x), ["status", "stats_summary"])):
            self.skip_history_when_saving = True

        try:
            super().save(*args, **kwargs)
        finally:
            if hasattr(self, "skip_history_when_saving"):
                del self.skip_history_when_saving

        if is_adding:
            self._rebuild_history(
                status_changes=self.get_status_changes(),
                stats_summary_changes=self.get_stats_summary_changes(),
            )

    # Meta and String
    class Meta(TimeStampedModel.Meta):
        verbose_name = _("specie distribution")
        verbose_name_plural = _("species distribution")
        constraints = TimeStampedModel.Meta.constraints + [
            models.UniqueConstraint(fields=["boundary", "taxon", "source"], name="unique_boundary_taxon_source"),
            models.CheckConstraint(
                check=models.Q(status_since__lte=Now()), name="status_since_cannot_be_future_dated"
            ),
        ]

    def __str__(self) -> str:
        # See: https://github.com/jazzband/django-simple-history/issues/533
        #      https://github.com/jazzband/django-simple-history/issues/521
        # return f"[{self.get_source_display()}]: {self.get_status_display()}"
        return super().__str__()
