from collections import defaultdict, Counter
from decimal import Decimal, localcontext
import numbers
from typing import List, Optional, Dict, Any, Tuple

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.base import ModelBase
from django.contrib.auth import get_user_model
from datetime import timedelta
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from taggit.managers import TaggableManager

from django_lifecycle import LifecycleModel, hook, AFTER_SAVE, AFTER_CREATE
from django_lifecycle.conditions import WhenFieldValueChangesTo, WhenFieldHasChanged

from mosquito_alert.geo.models import EuropeCountry
from mosquito_alert.workspaces.models import Workspace, WorkspaceMembership
from mosquito_alert.reports.models import Report, Photo
from mosquito_alert.taxa.models import Taxon

from .managers import ExpertReportAnnotationManager, IdentificationTaskManager
from .messages import (
    other_insect_msg_dict,
    albopictus_msg_dict,
    albopictus_probably_msg_dict,
    culex_msg_dict,
)
from .stats import calculate_norm_entropy

User = get_user_model()


def get_confidence_label(value: numbers.Number) -> str:
    value = float(value)
    if value >= 0.9:
        return _("species_value_confirmed")
    elif value >= 0.5:
        return _("species_value_possible")
    else:
        return _("Not sure")


def get_is_high_confidence(value: numbers.Number) -> bool:
    return float(value) >= 0.9


class IdentificationTask(LifecycleModel):
    @classmethod
    def get_or_create_for_report(
        self, report
    ) -> Tuple[Optional["IdentificationTask"], bool]:
        if not report.photos.exists() or not report.type == Report.TYPE_ADULT:
            return None, False

        return self.objects.get_or_create(
            report=report, defaults={"photo": report.photos.first()}
        )

    @classmethod
    def get_taxon_consensus(
        cls, annotations: List["ExpertReportAnnotation"], min_confidence: float = 0.5
    ) -> Tuple[Optional[Taxon], Decimal, float, float]:
        """
        Determines the most probable taxon based on expert annotations, calculating confidence,
        uncertainty, and agreement using a taxonomic hierarchy. Confidence is propagated from leaves
        to parents, and uncertainty is measured using normalized entropy.

        Parameters:
            annotations (List['ExpertReportAnnotation']): List of expert annotations, each containing a taxon and its confidence level.
            min_confidence (float): Minimum confidence threshold to consider a taxon as final.

        Returns:
            Tuple[Optional['Taxon'], float, float, float]:
                - Most probable taxon (or None if unclassified).
                - Associated confidence score.
                - Normalized entropy (uncertainty measure).
                - Agreement score (proportion of annotations agreeing with the selected taxon).
        """

        def distribute_confidence_leaves(taxon: Taxon, confidence: Decimal) -> None:
            """
            Distributes the given confidence value to the leaf taxa under the provided taxon.
            If the taxon is a leaf itself, the confidence is added directly. Otherwise, the
            confidence is distributed evenly among its leaves.
            """
            if taxon.is_leaf():
                taxon_leaves_confidence[taxon] += confidence
                return

            # TODO: distribute first to children instead of directly to leaves?
            taxon_leaves_qs = taxon.get_leaves()
            num_leaves = taxon_leaves_qs.count()
            for taxon_leaf in taxon_leaves_qs.iterator(chunk_size=1000):
                taxon_leaves_confidence[taxon_leaf] += confidence / num_leaves

        def propagate_confidence_up(
            taxon_confidence: defaultdict[Decimal],
        ) -> defaultdict[Decimal]:
            """
            Propagates confidence values upwards from leaves to their parent taxa recursively.

            Parameters:
                taxon_confidence (defaultdict): A dictionary with taxa as keys and their corresponding confidence values.

            Returns:
                defaultdict: The propagated confidence values for each taxon.
            """

            # Cache for storing already fetched ancestors
            ancestor_cache = {}
            ancestors_confidence = defaultdict(Decimal)

            for taxon, confidence in taxon_confidence.items():
                # Find an existing sibling in the cache
                t_ancestors = next(
                    (
                        value
                        for key, value in ancestor_cache.items()
                        if taxon.is_sibling_of(key)
                    ),
                    None,
                )

                if not t_ancestors:
                    t_ancestors = list(taxon.get_ancestors())
                    ancestor_cache[taxon] = t_ancestors

                for t_ancestor in t_ancestors:
                    ancestors_confidence[t_ancestor] += confidence

            return defaultdict(
                Decimal, Counter(taxon_confidence) + Counter(ancestors_confidence)
            )

        # Step 1: Handle edge cases where no annotations are available.
        if not annotations:
            # Unclassified. No annotations yet.
            return None, 0.0, 1.0, 0.0

        total_annotations = len(annotations)
        annotations_with_taxon = [
            annotation for annotation in annotations if annotation.taxon
        ]

        if not annotations_with_taxon:
            # Unclassified. Not an insect.
            return None, 1.0, 0.0, 1.0

        num_annotations_with_taxon = len(annotations_with_taxon)
        total_null_annotations = total_annotations - num_annotations_with_taxon

        # Step 2: Initialize data structures.
        taxon_leaves_confidence = defaultdict(Decimal)
        taxon_agreement = defaultdict(float)
        taxon_agreement[None] = total_null_annotations / total_annotations

        # Step 3: Aggregate confidences.
        for annotation in annotations_with_taxon:
            taxon, confidence = annotation.taxon, Decimal(str(annotation.confidence))
            taxon_agreement[taxon] += 1 / total_annotations

            # Distribute given confidence to leaves.
            distribute_confidence_leaves(taxon=taxon, confidence=confidence)

            # Distribute remaining confidence among sibling leaves.
            remaining_confidence = 1 - confidence
            if remaining_confidence > 0:
                # Getting siblings from the same rank group.
                siblings_qs = taxon.get_sibling_leaves_in_rank_group()
                num_siblings = siblings_qs.count()
                for sibling in siblings_qs:
                    distribute_confidence_leaves(
                        taxon=sibling, confidence=remaining_confidence / num_siblings
                    )

        # Step 4: Propagate confidence up the taxonomy.
        aggregated_confidence = propagate_confidence_up(taxon_leaves_confidence)
        with localcontext() as ctx:
            ctx.prec = cls._meta.get_field("confidence").max_digits

            normalized_confidence = {
                taxon: confidence / num_annotations_with_taxon
                for taxon, confidence in aggregated_confidence.items()
            }

        # Step 5: Select the best taxon above the confidence threshold.
        valid_taxa = [
            (taxon, conf)
            for taxon, conf in normalized_confidence.items()
            if conf >= float(min_confidence)
        ]

        if not valid_taxa:
            # No taxa meet the minimum confidence threshold.
            return None, 0.0, 1.0, 0.0

        result_taxon, result_confidence = max(
            valid_taxa,
            # NOTE: until we don't have a full taxonomy tree, use agreement first.
            key=lambda item: (taxon_agreement.get(item[0], 0), item[0].rank, item[1]),
            # key=lambda item: (item[0].rank_group, taxon_agreement.get(item[0], 0), item[1])
        )
        result_agreement = taxon_agreement.get(result_taxon, 0)

        # Step 6: Calculate uncertainty (normalized entropy).
        # For the probability distribution we will only consider the leaves of the rank group.
        sibling_pks = result_taxon.get_sibling_leaves_in_rank_group().values_list(
            "pk", flat=True
        )
        probabilities = [result_confidence] + [
            confidence
            for taxon, confidence in normalized_confidence.items()
            if taxon.pk in sibling_pks
        ]
        norm_entropy = calculate_norm_entropy(probabilities)
        return result_taxon, result_confidence, norm_entropy, result_agreement

    class Status(models.TextChoices):
        # OPEN STATUS
        OPEN = "open", _("Open")
        CONFLICT = "conflict", _("Conflict")
        REVIEW = "review", _("Review")

        # DONE STATUS
        DONE = "done", _("Done")
        ARCHIVED = "archived", _("Archived")  # For soft-deleted reports or hidden

    class Review(models.TextChoices):
        AGREE = "agree", _("Agreed with experts")
        OVERWRITE = "overwrite", _("Overwritten")

    class ResultSource(models.TextChoices):
        EXPERT = "expert", _("Expert")
        AI = "ai", _("Artificial Intelligence")

    CLOSED_STATUS = [Status.DONE, Status.ARCHIVED]

    report = models.OneToOneField(
        Report,
        primary_key=True,
        related_name="identification_task",
        on_delete=models.CASCADE,
        limit_choices_to={"type": "adult"},
    )
    photo = models.ForeignKey(
        Photo,
        related_name="identification_tasks",
        on_delete=models.CASCADE,
        editable=False,
    )

    assignees = models.ManyToManyField(
        User,
        through="identification_tasks.ExpertReportAnnotation",
        through_fields=("identification_task", "user"),
    )

    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.OPEN, db_index=True
    )
    is_flagged = models.BooleanField(default=False, editable=False)

    is_safe = models.BooleanField(
        default=False,
        editable=False,
        help_text="Indicates if the content is safe for publication.",
    )

    public_note = models.TextField(null=True, blank=True, editable=False)
    message_for_user = models.TextField(null=True, blank=True, editable=False)

    total_annotations = models.PositiveSmallIntegerField(
        default=0, editable=False
    )  # total experts
    total_finished_annotations = models.PositiveSmallIntegerField(
        default=0, editable=False
    )  # when is_finished = True (only for experts)

    result_source = models.CharField(
        max_length=8,
        choices=ResultSource.choices,
        editable=False,
        blank=True,
        null=True,
    )

    # Review
    review_type = models.CharField(
        max_length=16,
        choices=Review.choices,
        default=None,
        editable=False,
        blank=True,
        null=True,
    )
    reviewed_at = models.DateTimeField(null=True, blank=True, editable=False)
    reviewed_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        editable=False,
        on_delete=models.SET_NULL,
        related_name="identification_tasks_reviewed",
    )

    pred_insect_confidence = models.FloatField(
        null=True,
        blank=True,
        editable=False,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="The insect confidence from the predictions.",
    )

    taxon = models.ForeignKey(
        Taxon, on_delete=models.PROTECT, null=True, blank=True, editable=False
    )
    confidence = models.DecimalField(
        max_digits=7,
        decimal_places=6,
        default=Decimal("0"),
        editable=False,
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("1"))],
    )
    uncertainty = models.FloatField(
        default=1.0,
        editable=False,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
    )
    agreement = models.FloatField(
        default=0,
        editable=False,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
    )

    sex = models.CharField(
        max_length=10,
        choices=[("male", "Male"), ("female", "Female")],
        null=True,
        blank=True,
        editable=False,
        default=None,
    )
    is_blood_fed = models.BooleanField(
        null=True, blank=True, editable=False, default=None
    )
    is_gravid = models.BooleanField(null=True, blank=True, editable=False, default=None)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    objects = IdentificationTaskManager()

    @cached_property
    def annotators(self) -> models.QuerySet:
        return self.assignees.filter(pk__in=self.annotations.values("user")).order_by(
            "expert_report_annotations__created"
        )

    @cached_property
    def annotations(self) -> models.QuerySet:
        return self.expert_report_annotations.all().completed()

    @property
    def confidence_label(self) -> str:
        # TODO: check that API does not fix this as enum. This changes according to language.
        return get_confidence_label(value=self.confidence)

    @cached_property
    def country(self) -> Optional[EuropeCountry]:
        return self.report.country

    # LEGACY
    @property
    def is_high_confidence(self) -> bool:
        if not self.confidence:
            return False
        return get_is_high_confidence(value=self.confidence)

    @cached_property
    def exclusivity_end(self) -> Optional[timezone.datetime]:
        if not self.country:
            return None

        country_workspace = Workspace.objects.filter(country=self.country).first()
        if not country_workspace:
            return None

        supervisors_qs = WorkspaceMembership.objects.filter(
            workspace=country_workspace, role=WorkspaceMembership.Role.SUPERVISOR
        )
        if supervisors_qs.exists():
            return self.report.server_upload_time + timedelta(
                days=country_workspace.supervisor_exclusivity_days
            )
        return None

    @property
    def in_exclusivity_period(self) -> bool:
        exclusivity_end = self.exclusivity_end
        return exclusivity_end and timezone.now() < exclusivity_end

    @property
    def is_done(self) -> bool:
        return self.status == self.Status.DONE

    @property
    def is_reviewed(self) -> bool:
        return bool(self.reviewed_at)

    def _update_from_annotation(
        self, annotation: "ExpertReportAnnotation", default_status: str
    ) -> None:
        """Helper function to update attributes from an annotation."""
        self.result_source = self.ResultSource.EXPERT
        self.photo_id = annotation.best_photo_id
        self.public_note = annotation.public_note
        self.message_for_user = annotation.message_for_user
        self.taxon, self.confidence, self.uncertainty, self.agreement = (
            self.get_taxon_consensus(
                annotations=[
                    annotation,
                ]
            )
        )
        self.is_safe = annotation.status != ExpertReportAnnotation.Status.HIDDEN
        self.status = default_status
        self.is_flagged = annotation.status == ExpertReportAnnotation.Status.FLAGGED
        self.sex = annotation.sex
        self.is_gravid = annotation.is_gravid
        self.is_blood_fed = annotation.is_blood_fed

    def _update_from_photo_prediction(
        self, photo_prediction: "PhotoPrediction"
    ) -> None:
        self.result_source = self.ResultSource.AI
        self.photo_id = photo_prediction.photo_id
        self.taxon = photo_prediction.taxon
        self.confidence = photo_prediction.confidence
        self.uncertainty = photo_prediction.uncertainty
        self.agreement = 1
        self.is_safe = True
        self.status = self.Status.DONE
        self.is_flagged = False

    def assign_to_user(self, user: User) -> None:
        """Assign the task to a user."""

        # NOTE: do not use self.assignees.add. The 'through' model
        #       will be created using bulk_create, so it won't call
        #       save().

        ExpertReportAnnotation.objects.get_or_create(
            identification_task=self,
            user=user,
            defaults={
                "is_finished": False,
            },
        )

    def get_display_identification_label(self) -> str:
        if not self.is_done or not self.taxon:
            return _("species_unclassified")
        if self.taxon.is_root():
            return _("species_notsure")

        return self.taxon.get_display_friendly_common_name()

    def _reset_fields(self) -> None:
        # Back to defaults. e.g: when ExpertReportAnnotation delete
        self.status = self._meta.get_field("status").default
        self.public_note = None
        self.message_for_user = None
        self.taxon = None
        self.result_source = None
        self.confidence = self._meta.get_field("confidence").default
        self.uncertainty = self._meta.get_field("uncertainty").default
        self.agreement = self._meta.get_field("agreement").default
        self.is_safe = self._meta.get_field("is_safe").default
        self.is_flagged = self._meta.get_field("is_flagged").default
        self.sex = self._meta.get_field("sex").default
        self.is_gravid = self._meta.get_field("is_gravid").default
        self.is_blood_fed = self._meta.get_field("is_blood_fed").default
        self.review_type = None
        self.reviewed_at = None
        self.reviewed_by = None

    def refresh(self, force: bool = False) -> None:
        def get_most_voted_field(
            field_name: str,
            discard_nulls: bool = True,
            discard_blanks: bool = True,
            tie_break_field: Optional[str] = None,
            lookup_filter: Optional[Dict[str, Any]] = None,
        ) -> Optional[str]:
            """
            Get the most voted value for a specific field from finished expert annotations.
            In case of a tie, use the tie_break_field (if provided) to resolve the tie.
            """
            # Get the model of the queryset
            qs = finished_experts_annotations_qs
            if discard_nulls:
                qs = finished_experts_annotations_qs.filter(
                    **{f"{field_name}__isnull": False}
                )

            if discard_blanks:
                model = finished_experts_annotations_qs.model
                # Check the field type
                field = model._meta.get_field(field_name)
                # Only exclude empty strings for CharField or TextField
                if isinstance(field, (models.CharField, models.TextField)):
                    qs = qs.exclude(**{f"{field_name}__exact": ""})

            if lookup_filter:
                qs = qs.filter(**lookup_filter)

            # Annotate with vote count
            annotated_qs = qs.values(field_name).annotate(vote_count=models.Count(1))

            # If tie_break_field is provided, order by it after vote_count
            if tie_break_field:
                annotated_qs = annotated_qs.order_by("-vote_count", tie_break_field)
            else:
                annotated_qs = annotated_qs.order_by("-vote_count")

            return annotated_qs.values_list(field_name, flat=True).first()

        # NOTE: Do not remove! This is crucial.
        # When refresh() is called after saving ExpertReportAnnotation,
        # ExpertReportAnnotation.identification_task is returned before the refresh.
        # This means the annotation object may contain an outdated status of
        # identification_task.
        # If save() is called again, it would refresh an outdated version
        # of identification_task, potentially triggering unintended side effects,
        # such as executing the on_done() @hook multiple times and causing duplicate flows.
        # Therefore, regardless of the current state of identification_task,
        # we must always ensure we are working with the latest version from the database.
        self.refresh_from_db()

        # Querysets for expert annotations
        experts_annotations_qs = self.expert_report_annotations.exclude(
            decision_level=ExpertReportAnnotation.DecisionLevel.FINAL
        )
        finished_experts_annotations_qs = experts_annotations_qs.filter(
            is_finished=True
        )

        # Find executive and final annotations
        executive_annotation = (
            finished_experts_annotations_qs.filter(
                decision_level=ExpertReportAnnotation.DecisionLevel.EXECUTIVE
            )
            .order_by("-last_modified")
            .first()
        )
        final_annotation = (
            self.expert_report_annotations.filter(
                is_finished=True,
                decision_level=ExpertReportAnnotation.DecisionLevel.FINAL,
            )
            .order_by("-last_modified")
            .first()
        )

        # Photo predictions
        final_photo_prediction = self.photo_predictions.filter(is_decisive=True).first()

        if self.photo_predictions.exists():
            self.pred_insect_confidence = self.photo_predictions.aggregate(
                models.Max("insect_confidence")
            )["insect_confidence__max"]
        else:
            self.pred_insect_confidence = None

        # Update task statistics
        self.total_annotations = experts_annotations_qs.count()
        self.total_finished_annotations = finished_experts_annotations_qs.count()

        current_photo_id = self.photo_id
        if final_annotation:
            # Case 1: Review (overwrite)
            self._update_from_annotation(
                annotation=final_annotation, default_status=self.Status.DONE
            )
            self.reviewed_at = final_annotation.last_modified
            self.reviewed_by = final_annotation.user
            self.review_type = self.Review.OVERWRITE
        elif self.total_finished_annotations > 0:
            if not self.is_reviewed or force:
                # TODO: ensure annotations were created before review -> pending, there are annotations that not meet this requirement.
                if executive_annotation:
                    # Case 2: Executive validation
                    default_status = (
                        self.Status.DONE
                        if executive_annotation.status
                        == ExpertReportAnnotation.Status.PUBLIC
                        else self.Status.REVIEW
                    )
                    self._update_from_annotation(
                        annotation=executive_annotation, default_status=default_status
                    )
                else:
                    if (
                        self.total_finished_annotations
                        >= settings.MAX_N_OF_EXPERTS_ASSIGNED_PER_REPORT
                    ):
                        self.status = self.Status.DONE

                    # Case 3: Sufficient annotations for final decision
                    self.result_source = self.ResultSource.EXPERT
                    taxon, confidence, uncertainty, agreement = (
                        self.get_taxon_consensus(
                            annotations=list(finished_experts_annotations_qs)
                        )
                    )
                    if uncertainty > 0.92:
                        self.taxon = Taxon.get_root()
                        self.confidence = Decimal("1.0")
                        self.uncertainty = 1.0
                        self.agreement = 0.0
                        self.status = self.Status.CONFLICT
                    else:
                        self.taxon = taxon
                        self.confidence = confidence
                        self.uncertainty = uncertainty
                        self.agreement = agreement

                        if (
                            self.agreement == 0
                            and finished_experts_annotations_qs.filter(
                                taxon__is_relevant=True
                            ).exists()
                        ):
                            # All experts has choosen different things.
                            self.status = self.Status.CONFLICT

                    if self.taxon:
                        taxon_filter = {"taxon__in": Taxon.get_tree(parent=self.taxon)}
                    else:
                        taxon_filter = {"taxon__isnull": True}
                    self.photo_id = get_most_voted_field(
                        field_name="best_photo",
                        lookup_filter=taxon_filter,
                        tie_break_field="-is_simplified",  # In the case of tie, the extended version has prevalence.
                    )
                    self.public_note = get_most_voted_field(
                        field_name="public_note", lookup_filter=taxon_filter
                    )
                    self.sex = get_most_voted_field(
                        field_name="sex",
                        tie_break_field="-is_simplified",  # In the case of tie, the extended version has prevalence.
                    )
                    self.is_blood_fed = get_most_voted_field(
                        field_name="is_blood_fed",
                        lookup_filter={"sex": self.sex},
                        tie_break_field="-is_simplified",  # In the case of tie, the extended version has prevalence.
                    )
                    self.is_gravid = get_most_voted_field(
                        field_name="is_gravid",
                        lookup_filter={"sex": self.sex},
                        tie_break_field="-is_simplified",  # In the case of tie, the extended version has prevalence.
                    )

                    self.is_safe = not finished_experts_annotations_qs.filter(
                        status=ExpertReportAnnotation.Status.HIDDEN
                    ).exists()
                    self.is_flagged = finished_experts_annotations_qs.filter(
                        status=ExpertReportAnnotation.Status.FLAGGED
                    ).exists()

                    if not self.is_safe or self.is_flagged:
                        self.status = self.Status.REVIEW
        elif final_photo_prediction:
            self._update_from_photo_prediction(photo_prediction=final_photo_prediction)
        else:
            self._reset_fields()

        # Ensure photo_id is updated and save the instance
        self.photo_id = self.photo_id or current_photo_id

        self.save()

    @hook(
        AFTER_SAVE,
        condition=WhenFieldValueChangesTo("status", value=Status.DONE),
    )
    def on_done(self) -> None:
        if self.result_source != self.ResultSource.EXPERT:
            return
        from .messaging import send_finished_identification_task_notification

        send_finished_identification_task_notification(
            identification_task=self, from_user=User.objects.filter(pk=25).first()
        )

    @hook(AFTER_CREATE)
    @hook(
        AFTER_SAVE,
        condition=WhenFieldHasChanged("status", has_changed=True)
        | WhenFieldHasChanged("is_safe", has_changed=True),
    )
    def refresh_report_published_at(self) -> None:
        old_value = self.report.published_at
        new_value = None
        if self.is_done and self.is_safe:
            new_value = timezone.now()

        if old_value != new_value:
            self.report.published_at = new_value
            self.report.save()

    def save(self, *args, **kwargs):
        if self.is_reviewed:
            self.status = self.Status.DONE
            if self.review_type == self.Review.AGREE:
                self.is_flagged = False

        if self.status == self.Status.CONFLICT:
            self.is_flagged = True

        if not self.report.is_browsable:
            self.status = self.Status.ARCHIVED

        super().save(*args, **kwargs)

    class Meta:
        db_table = "tigacrafting_identificationtask"  # NOTE: migrate from old tigacrafting, kept old name to avoid issues with custom third-party scripts that still uses the raw table name.
        permissions = [
            ("view_archived_identificationtasks", "Can view archived records"),
            ("add_review", "Can review"),
        ]
        indexes = [
            models.Index(fields=["taxon", "report"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(review_type__isnull=True)
                | (
                    models.Q(reviewed_at__isnull=False)
                    & models.Q(reviewed_by__isnull=False)
                ),
                name="review_requires_fields_if_set",
            ),
            models.CheckConstraint(
                check=models.Q(
                    total_finished_annotations__lte=models.F("total_annotations")
                ),
                name="total_finished_annotations_lte_total_annotations",
            ),
            models.CheckConstraint(
                check=models.Q(confidence__range=(Decimal("0"), Decimal("1"))),
                name="%(app_label)s_%(class)s_confidence_between_0_and_1",
            ),
            models.CheckConstraint(
                check=models.Q(uncertainty__range=(0, 1)),
                name="%(app_label)s_%(class)s_uncertainty_between_0_and_1",
            ),
            models.CheckConstraint(
                check=models.Q(agreement__range=(0, 1)),
                name="%(app_label)s_%(class)s_agreement_between_0_and_1",
            ),
            models.CheckConstraint(
                check=~(models.Q(sex="male") & models.Q(is_blood_fed=True)),
                name="%(app_label)s_%(class)s_blood_fed_only_if_female",
            ),
            models.CheckConstraint(
                check=~(models.Q(sex="male") & models.Q(is_gravid=True)),
                name="%(app_label)s_%(class)s_gravid_only_if_female",
            ),
        ]


class ExpertReportAnnotation(models.Model):
    class Status(models.IntegerChoices):
        PUBLIC = 1, "Public"
        FLAGGED = 0, "Flagged"
        HIDDEN = -1, "Hidden"

    class DecisionLevel(models.TextChoices):
        NORMAL = "normal", _("Normal")
        EXECUTIVE = "executive", _("Executive")
        FINAL = "final", _("Final")

    class ConfidenceCategory(float, models.Choices):
        DEFINITELY = 1, "definitely"
        PROBABLY = 0.75, "probably"

    # Relations
    user = models.ForeignKey(
        User,
        related_name="expert_report_annotations",
        on_delete=models.PROTECT,
    )
    identification_task = models.ForeignKey(
        IdentificationTask,
        editable=False,
        related_name="expert_report_annotations",
        on_delete=models.CASCADE,
    )
    best_photo = models.ForeignKey(
        Photo,
        related_name="expert_report_annotations",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    tags = TaggableManager(blank=True)
    taxon = models.ForeignKey(Taxon, null=True, blank=True, on_delete=models.PROTECT)

    status = models.IntegerField(
        "Status",
        choices=Status.choices,
        default=Status.PUBLIC,
        help_text="Whether report should be displayed on public map, flagged for further checking before public display), or hidden.",
    )

    internal_note = models.TextField(
        null=True, blank=True, help_text="Internal notes for yourself or other experts"
    )
    public_note = models.TextField(
        null=True, blank=True, help_text="Notes to display on public map"
    )
    message_for_user = models.TextField(
        null=True,
        blank=True,
        help_text="Message that user will receive when viewing report on phone",
    )

    is_finished = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Mark this when you have completed your review and are ready for your annotation to be displayed to public.",
    )
    linked_id = models.CharField(
        "Linked ID",
        max_length=10,
        help_text="Use this field to add any other ID that you want to associate the record with (e.g., from some other database).",
        blank=True,
    )
    is_simplified = models.BooleanField(
        default=False,
        help_text="If True, the report annotation interface shows less input controls",
    )

    decision_level = models.CharField(
        max_length=16, choices=DecisionLevel.choices, default=DecisionLevel.NORMAL
    )
    is_favourite = models.BooleanField(default=False)

    confidence = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    sex = models.CharField(
        max_length=10,
        choices=[("male", "Male"), ("female", "Female")],
        null=True,
        blank=True,
        default=None,
    )
    is_blood_fed = models.BooleanField(null=True, blank=True, default=None)
    is_gravid = models.BooleanField(null=True, blank=True, default=None)

    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_modified = models.DateTimeField(auto_now=True, editable=False)

    objects = ExpertReportAnnotationManager()

    class Meta:
        db_table = "tigacrafting_expertreportannotation"  # NOTE: migrate from old tigacrafting, kept old name to avoid issues with custom third-party scripts that still uses the raw table name.
        constraints = [
            models.UniqueConstraint(
                fields=["user", "identification_task"], name="unique_assignation"
            ),
            models.CheckConstraint(
                check=models.Q(confidence__gte=0) & models.Q(confidence__lte=1),
                name="expertreportannotation_confidence_between_0_and_1",
            ),
            models.CheckConstraint(
                check=~(models.Q(sex="male") & models.Q(is_blood_fed=True)),
                name="expertreportannotation_blood_fed_only_if_female",
            ),
            models.CheckConstraint(
                check=~(models.Q(sex="male") & models.Q(is_gravid=True)),
                name="expertreportannotation_gravid_only_if_female",
            ),
        ]

    @property
    def confidence_label(self):
        return get_confidence_label(value=self.confidence)

    @property
    def is_high_confidence(self) -> bool:
        if not self.confidence:
            return False
        return get_is_high_confidence(value=self.confidence)

    @classmethod
    def _get_auto_message(
        cls, taxon: Taxon, confidence: float, locale: str = "en"
    ) -> Optional[str]:
        msg_dict = other_insect_msg_dict
        if not taxon:
            return msg_dict.get(locale)

        if taxon.pk == 112:  # albopictus
            msg_dict = (
                albopictus_msg_dict
                if get_is_high_confidence(value=confidence)
                else albopictus_probably_msg_dict
            )
        elif taxon.pk == 10:  # culex
            msg_dict = culex_msg_dict

        return msg_dict.get(locale)

    def _can_be_simplified(self) -> bool:
        # If decision_level is Final -> False
        if self.decision_level == self.DecisionLevel.FINAL:
            return False

        # If the user is the supervisor of that country -> False
        is_country_supervisor = WorkspaceMembership.objects.filter(
            workspace__country=self.identification_task.country,
            user=self.user,
            role=WorkspaceMembership.Role.SUPERVISOR,
        ).exists()
        if is_country_supervisor:
            return False

        # Return False if no is_simplified found or if the objects to be
        # created is suposed to be the last.
        total_completed_annotations_qs = ExpertReportAnnotation.objects.filter(
            identification_task=self.identification_task
        )
        return (
            total_completed_annotations_qs.filter(is_simplified=False).exists()
            or total_completed_annotations_qs.count()
            < settings.MAX_N_OF_EXPERTS_ASSIGNED_PER_REPORT - 1
        )

    def save(self, *args, **kwargs):
        if not kwargs.pop("skip_lastmodified", False):
            self.last_modified = timezone.now()

        if self.taxon is None:
            self.confidence = 0.0

        # On create only
        if self._state.adding:
            _userstat = self.user.userstat
            _userstat.grabbed_reports += 1
            _userstat.save()
            if not self.is_finished:
                self.is_simplified = self._can_be_simplified()

        if self.is_simplified:
            self.message_for_user = None

        super(ExpertReportAnnotation, self).save(*args, **kwargs)

        self.identification_task.refresh()

    def delete(self, *args, **kwargs):
        identification_task = self.identification_task

        if self.decision_level == self.DecisionLevel.EXECUTIVE:
            ExpertReportAnnotation.objects.filter(
                identification_task=identification_task,
                is_finished=True,
                decision_level=self.DecisionLevel.NORMAL,
            ).delete()

        result = super().delete(*args, **kwargs)

        if identification_task:
            identification_task.refresh(force=True)

        return result


class PhotoClassifierScoresMeta(ModelBase):
    CLASS_FIELDNAMES_CHOICES = [
        ("ae_albopictus", "Aedes albopictus"),
        ("ae_aegypti", "Aedes aegypti"),
        ("ae_japonicus", "Aedes japonicus"),
        ("ae_koreicus", "Aedes koreicus"),
        ("culex", "Culex (s.p)"),
        ("anopheles", "Anopheles (s.p.)"),
        ("culiseta", "Culiseta (s.p.)"),
        ("other_species", "Ohter species"),
        ("not_sure", "Unidentifiable"),
    ]
    CLASS_UNCLASSIFIED = "not_sure"
    CLASS_FIELD_SUFFIX = "_score"

    def __new__(cls, name, bases, attrs, **kwargs):
        # Dynamically create FloatFields for each classifier result
        for fname, value in cls.CLASS_FIELDNAMES_CHOICES:
            # Apply suffix to the field names (will be overridden in subclasses)
            field_name = f"{fname}{cls.CLASS_FIELD_SUFFIX or ''}"
            attrs[field_name] = models.FloatField(
                validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
                help_text=f"Score value for the class {value}",
            )
        return super().__new__(cls, name, bases, attrs, **kwargs)


class PhotoPrediction(models.Model, metaclass=PhotoClassifierScoresMeta):
    CLASSIFIER_VERSION_CHOICES = [
        ("v2023.1", "v2023.1"),
        ("v2024.1", "v2024.1"),
        ("v2025.1", "v2025.1"),
        ("v2025.2", "v2025.2"),
        ("v2025.3", "v2025.3"),
        ("v2025.4", "v2025.4"),
    ]

    PREDICTED_CLASS_TO_TAXON = {
        "ae_aegypti": 113,
        "ae_albopictus": 112,
        "anopheles": 9,
        "culex": 10,
        "culiseta": 11,
        "ae_japonicus": 114,
        "ae_koreicus": 115,
        "other_species": 1,
        "not_sure": 1,
        None: None,
    }

    @classmethod
    def get_score_fieldnames(cls) -> List[str]:
        return [
            fname + cls.CLASS_FIELD_SUFFIX for fname, _ in cls.CLASS_FIELDNAMES_CHOICES
        ]

    photo = models.OneToOneField(
        Photo,
        primary_key=True,
        related_name="prediction",
        help_text="Photo to which the score refers to",
        on_delete=models.CASCADE,
    )
    identification_task = models.ForeignKey(
        IdentificationTask,
        related_name="photo_predictions",
        help_text="Identification task to which the photo belongs",
        on_delete=models.CASCADE,
    )
    taxon = models.ForeignKey(
        Taxon, null=True, blank=True, editable=True, on_delete=models.PROTECT
    )

    classifier_version = models.CharField(
        max_length=16, choices=CLASSIFIER_VERSION_CHOICES
    )
    is_decisive = models.BooleanField(
        default=False,
        help_text="Indicates if this prediction can close the identification task.",
    )

    insect_confidence = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Insect confidence",
    )

    # NOTE: will be null if "unclassified". For example when insect_confidence is very low.
    predicted_class = models.CharField(
        null=True,
        max_length=32,
        choices=PhotoClassifierScoresMeta.CLASS_FIELDNAMES_CHOICES,
        default=PhotoClassifierScoresMeta.CLASS_UNCLASSIFIED,
    )
    threshold_deviation = models.FloatField(
        validators=[MinValueValidator(-1.0), MaxValueValidator(1.0)],
    )

    x_tl = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="photo bounding box relative coordinates top left x",
    )
    x_br = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="photo bounding box relative coordinates bottom right x",
    )
    y_tl = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="photo bounding box relative coordinates top left y",
    )
    y_br = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="photo bounding box relative coordinates bottom right y",
    )

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    @property
    def confidence(self) -> float:
        return (
            getattr(self, f"{self.predicted_class}{type(self).CLASS_FIELD_SUFFIX}", 0.0)
            if self.predicted_class
            else 1.0
        )

    @property
    def uncertainty(self) -> float:
        return calculate_norm_entropy(
            probabilities=[
                getattr(self, fname) for fname in self.get_score_fieldnames()
            ]
        )

    def clean(self):
        if self.is_decisive:
            if self.taxon is None:
                raise ValidationError("Taxon must be set when is_decisive is True.")

            # NOTE: checking scores values inside self.is_decisive due to there are two cases
            #       when the scores can be all zero correctly:
            #       - 'Off-topic' (the picture is not a mosquito)
            #       - 'Unclassified' (the picture is a mosquito but none of the scores are above the threshold)
            if all(
                [getattr(self, fname) == 0.0 for fname in self.get_score_fieldnames()]
            ):
                raise ValidationError(
                    "All score fields cannot be zero when setting is_decisive is True."
                )

    def save(self, *args, **kwargs):
        self.taxon = Taxon.objects.filter(
            pk=self.PREDICTED_CLASS_TO_TAXON[self.predicted_class]
        ).first()

        self.clean()

        if self.is_decisive:
            # Be sure no other is_decisive are enabled.
            PhotoPrediction.objects.filter(
                identification_task=self.identification_task, is_decisive=True
            ).exclude(pk=self.pk).update(is_decisive=False)

        super().save(*args, **kwargs)

        self.identification_task.refresh()

    def delete(self, *args, **kwargs):
        identification_task = self.identification_task

        result = super().delete(*args, **kwargs)

        if identification_task:
            identification_task.refresh(force=True)

        return result

    class Meta:
        db_table = "tigacrafting_photoprediction"  # NOTE: migrate from old tigacrafting, kept old name to avoid issues with custom third-party scripts that still uses the raw table name.
        constraints = [
            # Ensure x_tl is less than or equal to x_br
            models.CheckConstraint(
                check=models.Q(x_tl__lte=models.F("x_br")), name="x_tl_less_equal_x_br"
            ),
            # Ensure y_tl is less than or equal to y_br
            models.CheckConstraint(
                check=models.Q(y_tl__lte=models.F("y_br")), name="y_tl_less_equal_y_br"
            ),
            # Ensure x_tl is between 0 and 1
            models.CheckConstraint(
                check=models.Q(x_tl__range=(0, 1)),
                name="%(app_label)s_%(class)s_x_tl_between_0_and_1",
            ),
            # Ensure x_br is between 0 and 1
            models.CheckConstraint(
                check=models.Q(x_br__range=(0, 1)),
                name="%(app_label)s_%(class)s_x_br_between_0_and_1",
            ),
            # Ensure y_tl is between 0 and 1
            models.CheckConstraint(
                check=models.Q(y_tl__range=(0, 1)),
                name="%(app_label)s_%(class)s_y_tl_between_0_and_1",
            ),
            # Ensure y_br is between 0 and 1
            models.CheckConstraint(
                check=models.Q(y_br__range=(0, 1)),
                name="%(app_label)s_%(class)s_y_br_between_0_and_1",
            ),
            # Ensure only one final prediction per task
            models.UniqueConstraint(
                fields=["identification_task"],
                condition=models.Q(is_decisive=True),
                name="unique_final_prediction_per_task",
            ),
            # Ensure each (photo, identification_task) combination is unique
            models.UniqueConstraint(
                fields=["photo", "identification_task"],
                name="unique_photo_identification_task",
            ),
        ]
