from collections import defaultdict, Counter
from decimal import Decimal, localcontext
import math
import numbers
from typing import List, Optional, Literal, Dict, Any, Tuple

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from django.contrib.auth import get_user_model
from datetime import timedelta
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from taggit.managers import TaggableManager
from django.db.models.signals import post_save
from django.dispatch import receiver

from django_lifecycle.conditions import WhenFieldValueChangesTo
from django_lifecycle import LifecycleModel, hook, AFTER_SAVE
from treebeard.mp_tree import MP_Node
from scipy.stats import entropy

import tigacrafting.html_utils as html_utils

from .managers import ExpertReportAnnotationManager, IdentificationTaskManager
from .messages import other_insect_msg_dict, albopictus_msg_dict, albopictus_probably_msg_dict, culex_msg_dict, notsure_msg_dict

User = get_user_model()

def score_computation(n_total, n_yes, n_no, n_unknown = 0, n_undefined =0):
    return float(n_yes - n_no)/n_total

def get_confidence_label(value: numbers.Number) -> str:
    value = float(value)
    if value >= 0.9:
        return _('species_value_confirmed')
    elif value >= 0.5:
        return _('species_value_possible')
    else:
        return _('Not sure')


class CrowdcraftingTask(models.Model):
    task_id = models.IntegerField(unique=True, null=True, default=None)
    photo = models.OneToOneField('tigaserver_app.Photo', on_delete=models.PROTECT, )

    def __unicode__(self):
        return str(self.task_id)

    def get_mosquito_validation_score(self):
        n_total = CrowdcraftingResponse.objects.filter(task=self).count()
        if n_total == 0:
            return None
        else:
            n_yes = CrowdcraftingResponse.objects.filter(task=self, mosquito_question_response='mosquito-yes').count()
            n_no = CrowdcraftingResponse.objects.filter(task=self, mosquito_question_response='mosquito-no').count()
            return score_computation(n_total=n_total, n_yes=n_yes, n_no=n_no)

    def get_tiger_validation_score(self):
        n_total = CrowdcraftingResponse.objects.filter(task=self).count()
        if n_total == 0:
            return None
        else:
            n_yes = CrowdcraftingResponse.objects.filter(task=self, tiger_question_response='tiger-yes').count()
            n_no = CrowdcraftingResponse.objects.filter(task=self, tiger_question_response='tiger-no').count() + CrowdcraftingResponse.objects.filter(task=self, tiger_question_response='undefined', mosquito_question_response='mosquito-no').count()
            return score_computation(n_total=n_total, n_yes=n_yes, n_no=n_no)

    def get_tiger_validation_score_cat(self):
        if self.get_tiger_validation_score() is not None:
            return int(round(2.499999 * self.get_tiger_validation_score(), 0))
        else:
            return None

    def get_site_validation_score(self):
        n_total = CrowdcraftingResponse.objects.filter(task=self).count()
        if n_total == 0:
            return None
        else:
            n_yes = CrowdcraftingResponse.objects.filter(task=self, site_question_response='site-yes').count()
            n_no = CrowdcraftingResponse.objects.filter(task=self, site_question_response='site-no').count()
            return score_computation(n_total=n_total, n_yes=n_yes, n_no=n_no)

    def get_site_validation_score_cat(self):
        if self.get_site_validation_score() is not None:
            return int(round(2.499999 * self.get_site_validation_score(), 0))
        else:
            return None

    def get_site_individual_responses_html(self):
        n_total = CrowdcraftingResponse.objects.filter(task=self).count()
        if n_total == 0:
            return None
        else:
            n_anon_yes = CrowdcraftingResponse.objects.filter(task=self, user__user_id=None, site_question_response='site-yes').count()
            n_anon_no = CrowdcraftingResponse.objects.filter(task=self, user__user_id=None, site_question_response='site-no').count()
            n_reg_yes = CrowdcraftingResponse.objects.filter(task=self, site_question_response='site-yes').exclude(user__user_id=None).count()
            n_reg_no = CrowdcraftingResponse.objects.filter(task=self, site_question_response='site-no').exclude(user__user_id=None).count()
            n_anon_unknown = CrowdcraftingResponse.objects.filter(task=self, user__user_id=None, site_question_response='site-unknown').count()
            n_anon_blank = CrowdcraftingResponse.objects.filter(task=self, user__user_id=None, site_question_response='undefined').count()
            n_reg_unknown = CrowdcraftingResponse.objects.filter(task=self, site_question_response='site-unknown').exclude(user__user_id=None).count()
            n_reg_blank = CrowdcraftingResponse.objects.filter(task=self, site_question_response='undefined').exclude(user__user_id=None).count()
            return '<table><tr><th>Resp.</th><th>Reg. Users</th><th>Anon. Users</th><th>Total</th></tr><tr><td>Yes</td><td>' + str(n_reg_yes) + '</td><td>' + str(n_anon_yes) + '</td><td>' + str(n_reg_yes + n_anon_yes) + '</td></tr><tr><td>No</td><td>' + str(n_reg_no) + '</td><td>' + str(n_anon_no) + '</td><td>' + str(n_reg_no + n_anon_no) + '</td></tr><tr><td>Not sure</td><td>' + str(n_reg_unknown) + '</td><td>' + str(n_anon_unknown) + '</td><td>' + str(0 + n_reg_unknown + n_anon_unknown) + '</td></tr><tr><td>Blank</td><td>' + str(n_reg_blank) + '</td><td>' + str(n_anon_blank) + '</td><td>' + str(n_reg_blank + n_anon_blank) + '</td></tr><tr><td>Total</td><td>' + str(n_reg_yes + n_reg_no + n_reg_unknown + n_reg_blank) + '</td><td>' + str(n_anon_yes + n_anon_no + n_anon_unknown + n_anon_blank) + '</td><td>' + str(n_anon_yes + n_anon_no + n_anon_unknown + n_anon_blank + n_reg_yes + n_reg_no + n_reg_unknown + n_reg_blank) + '</td></tr></table>'

    def get_tiger_individual_responses_html(self):
        n_total = CrowdcraftingResponse.objects.filter(task=self).count()
        if n_total == 0:
            return None
        else:
            n_anon_yes = CrowdcraftingResponse.objects.filter(task=self, user__user_id=None, tiger_question_response='tiger-yes').count()
            n_anon_no = CrowdcraftingResponse.objects.filter(task=self, user__user_id=None, tiger_question_response='tiger-no').count() + CrowdcraftingResponse.objects.filter(task=self, user__user_id=None, mosquito_question_response='mosquito-no', tiger_question_response='undefined').count()
            n_reg_yes = CrowdcraftingResponse.objects.filter(task=self, tiger_question_response='tiger-yes').exclude(user__user_id=None).count()
            n_reg_no = CrowdcraftingResponse.objects.filter(task=self, tiger_question_response='tiger-no').exclude(user__user_id=None).count() + CrowdcraftingResponse.objects.filter(task=self, mosquito_question_response='mosquito-no', tiger_question_response='undefined').exclude(user__user_id=None).count()
            n_anon_unknown = CrowdcraftingResponse.objects.filter(task=self, user__user_id=None, tiger_question_response='tiger-unknown').count()
            n_anon_blank = CrowdcraftingResponse.objects.filter(task=self, user__user_id=None, tiger_question_response='undefined').exclude(mosquito_question_response='mosquito-no').count()
            n_reg_unknown = CrowdcraftingResponse.objects.filter(task=self, tiger_question_response='tiger-unknown').exclude(user__user_id=None).count()
            n_reg_blank = CrowdcraftingResponse.objects.filter(task=self, tiger_question_response='undefined').exclude(mosquito_question_response='mosquito-no').exclude(user__user_id=None).count()
            return '<table><tr><th>Resp.</th><th>Reg. Users</th><th>Anon. Users</th><th>Total</th></tr><tr><td>Yes</td><td>' + str(n_reg_yes) + '</td><td>' + str(n_anon_yes) + '</td><td>' + str(n_reg_yes + n_anon_yes) + '</td></tr><tr><td>No</td><td>' + str(n_reg_no) + '</td><td>' + str(n_anon_no) + '</td><td>' + str(n_reg_no + n_anon_no) + '</td></tr><tr><td>Not sure</td><td>' + str(n_reg_unknown) + '</td><td>' + str(n_anon_unknown) + '</td><td>' + str(0 + n_reg_unknown + n_anon_unknown) + '</td></tr><tr><td>Blank</td><td>' + str(n_reg_blank) + '</td><td>' + str(n_anon_blank) + '</td><td>' + str(n_reg_blank + n_anon_blank) + '</td></tr><tr><td>Total</td><td>' + str(n_reg_yes + n_reg_no + n_reg_unknown + n_reg_blank) + '</td><td>' + str(n_anon_yes + n_anon_no + n_anon_unknown + n_anon_blank) + '</td><td>' + str(n_anon_yes + n_anon_no + n_anon_unknown + n_anon_blank + n_reg_yes + n_reg_no + n_reg_unknown + n_reg_blank) + '</td></tr></table>'

    def get_mosquito_individual_responses_html(self):
        n_total = CrowdcraftingResponse.objects.filter(task=self).count()
        if n_total == 0:
            return None
        else:
            n_anon_yes = CrowdcraftingResponse.objects.filter(task=self, user__user_id=None, mosquito_question_response='mosquito-yes').count()
            n_anon_no = CrowdcraftingResponse.objects.filter(task=self, user__user_id=None, mosquito_question_response='mosquito-no').count()
            n_reg_yes = CrowdcraftingResponse.objects.filter(task=self, mosquito_question_response='mosquito-yes').exclude(user__user_id=None).count()
            n_reg_no = CrowdcraftingResponse.objects.filter(task=self, mosquito_question_response='mosquito-no').exclude(user__user_id=None).count()
            n_anon_unknown = CrowdcraftingResponse.objects.filter(task=self, user__user_id=None, mosquito_question_response='mosquito-unknown').count()
            n_anon_blank = CrowdcraftingResponse.objects.filter(task=self, user__user_id=None, mosquito_question_response='undefined').count()
            n_reg_unknown = CrowdcraftingResponse.objects.filter(task=self, mosquito_question_response='mosquito-unknown').exclude(user__user_id=None).count()
            n_reg_blank = CrowdcraftingResponse.objects.filter(task=self, mosquito_question_response='undefined').exclude(user__user_id=None).count()
            return '<table><tr><th>Resp.</th><th>Reg. Users</th><th>Anon. Users</th><th>Total</th></tr><tr><td>Yes</td><td>' + str(n_reg_yes) + '</td><td>' + str(n_anon_yes) + '</td><td>' + str(n_reg_yes + n_anon_yes) + '</td></tr><tr><td>No</td><td>' + str(n_reg_no) + '</td><td>' + str(n_anon_no) + '</td><td>' + str(n_reg_no + n_anon_no) + '</td></tr><tr><td>Not sure</td><td>' + str(n_reg_unknown) + '</td><td>' + str(n_anon_unknown) + '</td><td>' + str(0 + n_reg_unknown + n_anon_unknown) + '</td></tr><tr><td>Blank</td><td>' + str(n_reg_blank) + '</td><td>' + str(n_anon_blank) + '</td><td>' + str(n_reg_blank + n_anon_blank) + '</td></tr><tr><td>Total</td><td>' + str(n_reg_yes + n_reg_no + n_reg_unknown + n_reg_blank) + '</td><td>' + str(n_anon_yes + n_anon_no + n_anon_unknown + n_anon_blank) + '</td><td>' + str(n_anon_yes + n_anon_no + n_anon_unknown + n_anon_blank + n_reg_yes + n_reg_no + n_reg_unknown + n_reg_blank) + '</td></tr></table>'

    def get_crowdcrafting_n_responses(self):
        return CrowdcraftingResponse.objects.filter(task=self).count()

    mosquito_validation_score = property(get_mosquito_validation_score)
    tiger_validation_score = property(get_tiger_validation_score)
    site_validation_score = property(get_site_validation_score)
    site_individual_responses_html = property(get_site_individual_responses_html)
    tiger_individual_responses_html = property(get_tiger_individual_responses_html)
    mosquito_individual_responses_html = property(get_mosquito_individual_responses_html)
    crowdcrafting_n_responses = property(get_crowdcrafting_n_responses)
    tiger_validation_score_cat = property(get_tiger_validation_score_cat)
    site_validation_score_cat = property(get_site_validation_score_cat)


class CrowdcraftingUser(models.Model):
    user_id = models.IntegerField(blank=True, null=True)

    def __unicode__(self):
        return str(self.id)


class CrowdcraftingResponse(models.Model):
    response_id = models.IntegerField()
    task = models.ForeignKey('tigacrafting.CrowdcraftingTask', related_name="responses", on_delete=models.CASCADE, )
    user = models.ForeignKey('tigacrafting.CrowdcraftingUser', related_name="responses", blank=True, null=True, on_delete=models.SET_NULL, )
    user_lang = models.CharField(max_length=10, blank=True)
    mosquito_question_response = models.CharField(max_length=100)
    tiger_question_response = models.CharField(max_length=100)
    site_question_response = models.CharField(max_length=100)
    created = models.DateTimeField(blank=True, null=True)
    finish_time = models.DateTimeField(blank=True, null=True)
    user_ip = models.GenericIPAddressField(blank=True, null=True)

    def __unicode__(self):
        return str(self.id)

class IdentificationTask(LifecycleModel):
    @classmethod
    def create_for_report(self, report) -> Optional['IdentificationTask']:
        from tigaserver_app.models import Report
        if not report.photos.exists() or not report.type==Report.TYPE_ADULT:
            return None

        return self.objects.create(
            report=report,
            photo=report.photos.first()
        )

    @classmethod
    def get_taxon_consensus(
            cls,
            annotations: List['ExpertReportAnnotation'],
            min_confidence: float = 0.5
        ) -> Tuple[Optional['Taxon'], Decimal, float, float]:
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
            for taxon_leaf in taxon_leaves_qs.iterator():
                taxon_leaves_confidence[taxon_leaf] += confidence/num_leaves

        def propagate_confidence_up(taxon_confidence: defaultdict[Decimal]) -> defaultdict[Decimal]:
            """
            Propagates confidence values upwards from leaves to their parent taxa recursively.

            Parameters:
                taxon_confidence (defaultdict): A dictionary with taxa as keys and their corresponding confidence values.

            Returns:
                defaultdict: The propagated confidence values for each taxon.
            """
            parent_confidence = defaultdict(Decimal)
            for taxon, confidence in taxon_confidence.items():
                if t_parent:=taxon.parent:
                    parent_confidence[t_parent] += confidence
            if parent_confidence:
                # Recursively aggregate parent confidence values
                return defaultdict(
                    Decimal,
                    Counter(taxon_confidence) + Counter(propagate_confidence_up(parent_confidence))
                )
            return taxon_confidence

        def calculate_norm_entropy(probabilities: List[numbers.Number]) -> float:
            """Computes normalized entropy of the given probability distribution."""
            # Cast the probabilities list to a list of floats
            probabilities = [float(p) for p in probabilities]

            # If there's only one probability, there is no uncertainty (entropy = 0)
            # math.log2(1) = 0 -> would raise in the division (denominator)
            if len(probabilities) <= 1:
                return 0.0
            return entropy(probabilities, base=2) / math.log2(len(probabilities))

        # Step 1: Handle edge cases where no annotations are available.
        if not annotations:
            # Unclassified. No annotations yet.
            return None, 0.0, 1.0, 0.0

        total_annotations = len(annotations)
        annotations_with_taxon = [annotation for annotation in annotations if annotation.taxon]

        if not annotations_with_taxon:
            # Unclassified. Not an insect.
            return None, 1.0, 0.0, 1.0

        num_annotations_with_taxon = len(annotations_with_taxon)
        total_null_annotations = total_annotations - num_annotations_with_taxon

        # Step 2: Initialize data structures.
        taxon_leaves_confidence = defaultdict(Decimal)
        taxon_agreement = defaultdict(float)
        taxon_agreement[None] =  total_null_annotations/total_annotations

        # Step 3: Aggregate confidences.
        for annotation in annotations_with_taxon:
            taxon, confidence = annotation.taxon, Decimal(str(annotation.confidence))
            taxon_agreement[taxon] += 1/total_annotations

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
                        taxon=sibling,
                        confidence=remaining_confidence/num_siblings
                    )

        # Step 4: Propagate confidence up the taxonomy.
        aggregated_confidence = propagate_confidence_up(taxon_leaves_confidence)
        with localcontext() as ctx:
            ctx.prec = cls._meta.get_field('confidence').max_digits

            normalized_confidence = {
                taxon: confidence / num_annotations_with_taxon
                for taxon, confidence in aggregated_confidence.items()
            }

        # Step 5: Select the best taxon above the confidence threshold.
        valid_taxa = [
            (taxon, conf) for taxon, conf in normalized_confidence.items()
            if conf >= float(min_confidence)
        ]

        if not valid_taxa:
            # No taxa meet the minimum confidence threshold.
            return None, 0.0, 1.0, 0.0

        result_taxon, result_confidence = max(
            valid_taxa,
            # NOTE: until we don't have a full taxonomy tree, use agreement first.
            key=lambda item: (taxon_agreement.get(item[0], 0), item[0].rank, item[1])
            #key=lambda item: (item[0].rank_group, taxon_agreement.get(item[0], 0), item[1])
        )
        result_agreement = taxon_agreement.get(result_taxon, 0)

        # Step 6: Calculate uncertainty (normalized entropy).
        # For the probability distribution we will only consider the leaves of the rank group.
        sibling_pks = result_taxon.get_sibling_leaves_in_rank_group().values_list('pk', flat=True)
        probabilities = [result_confidence] + [
            confidence for taxon, confidence in normalized_confidence.items() if taxon.pk in sibling_pks
        ]
        norm_entropy = calculate_norm_entropy(probabilities)
        return result_taxon, result_confidence, norm_entropy, result_agreement


    class Status(models.TextChoices):
        # OPEN STATUS
        OPEN = 'open', _('Open')
        CONFLICT = 'conflict', _('Conflict')
        FLAGGED = 'flagged', _('Flagged')
        REVIEW = 'review', _('Review')

        # DONE STATUS
        DONE = 'done', _('Done')
        ARCHIVED = 'archived', _('Archived')  # For soft-deleted reports or hidden

    class Revision(models.TextChoices):
        AGREE = 'agree', _("Agreed with experts")
        OVERWRITE = 'overwrite', _("Overwritten")

    CLOSED_STATUS = [Status.DONE, Status.ARCHIVED]

    report = models.OneToOneField('tigaserver_app.Report', primary_key=True, related_name='identification_task', on_delete=models.CASCADE, limit_choices_to={'type': 'adult'})
    photo = models.ForeignKey('tigaserver_app.Photo', related_name='identification_tasks', on_delete=models.CASCADE, editable=False)

    assignees = models.ManyToManyField(
        User,
        through="tigacrafting.ExpertReportAnnotation",
        through_fields=("identification_task", "user"),
    )

    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN, db_index=True)

    is_safe = models.BooleanField(default=False, editable=False, help_text="Indicates if the content is safe for publication.")

    public_note = models.TextField(null=True, blank=True, editable=False)
    message_for_user = models.TextField(null=True, blank=True, editable=False)

    total_annotations = models.PositiveSmallIntegerField(default=0, editable=False) # total experts
    total_finished_annotations = models.PositiveSmallIntegerField(default=0, editable=False) # when validation_complete = True (only for experts)

    # Revision
    revision_type = models.CharField(max_length=16, choices=Revision.choices, default=None, editable=False, blank=True, null=True)
    reviewed_at = models.DateTimeField(null=True, blank=True, editable=False)

    taxon = models.ForeignKey('Taxon', on_delete=models.PROTECT, null=True, blank=True, editable=False)
    confidence = models.DecimalField(
        max_digits=7, decimal_places=6, default=Decimal("0"), editable=False,
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("1"))]
    )
    uncertainty = models.FloatField(default=1.0, editable=False, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    agreement = models.FloatField(default=0, editable=False, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    objects = IdentificationTaskManager()

    @property
    def confidence_label(self) -> str:
        return get_confidence_label(value=self.confidence)

    # LEGACY
    @property
    def validation_value(self) -> Optional[int]:
        if not self.taxon:
            return

        if not isinstance(self.taxon.content_object, Categories):
            return

        if not self.taxon.content_object.specify_certainty_level:
            return

        if self.confidence >= Decimal('0.9'):
            return ExpertReportAnnotation.VALIDATION_CATEGORY_DEFINITELY
        return ExpertReportAnnotation.VALIDATION_CATEGORY_PROBABLY

    @cached_property
    def exclusivity_end(self) -> Optional[timezone.datetime]:
        country = self.report.country
        if country and UserStat.objects.filter(national_supervisor_of=country).exists():
            return self.report.server_upload_time + timedelta(days=country.national_supervisor_report_expires_in)
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

    def _update_from_annotation(self, annotation: 'ExpertReportAnnotation', default_status: str) -> None:
        """Helper function to update attributes from an annotation."""
        self.photo_id = annotation.best_photo_id
        self.public_note = annotation.edited_user_notes
        self.message_for_user = annotation.message_for_user
        self.taxon, self.confidence, self.uncertainty, self.agreement = self.get_taxon_consensus(
            annotations=[annotation,]
        )
        self.is_safe = annotation.status == ExpertReportAnnotation.STATUS_PUBLIC
        self.status = default_status

    def assign_to_user(self, user: User) -> None:
        """Assign the task to a user."""

        # NOTE: do not use self.assignees.add. The 'through' model
        #       will be created using bulk_create, so it won't call
        #       save().

        ExpertReportAnnotation.objects.get_or_create(
            report=self.report,
            identification_task=self,
            user=user
        )

    def get_display_identification_label(self) -> str:
        if not self.is_done:
            return _("species_unclassified")
        if not self.taxon:
            return _("species_notsure")

        return self.taxon.get_display_friendly_common_name()

    def refresh(self, force: bool = False, commit: bool = True) -> None:
        def get_most_voted_field(
                field_name: str,
                discard_nulls: bool = True,
                discard_blanks: bool = True,
                tie_break_field: Optional[str] = None,
                lookup_filter: Optional[Dict[str, Any]] = None
            ) -> Optional[str]:
            """
            Get the most voted value for a specific field from finished expert annotations.
            In case of a tie, use the tie_break_field (if provided) to resolve the tie.
            """
            # Get the model of the queryset
            qs = finished_experts_annotations_qs
            if discard_nulls:
                qs = finished_experts_annotations_qs.filter(
                    **{f'{field_name}__isnull': False}
                )

            if discard_blanks:
                model = finished_experts_annotations_qs.model
                # Check the field type
                field = model._meta.get_field(field_name)
                # Only exclude empty strings for CharField or TextField
                if isinstance(field, (models.CharField, models.TextField)):
                    qs = qs.exclude(**{f'{field_name}__exact': ''})

            if lookup_filter:
                qs = qs.filter(**lookup_filter)

            # Annotate with vote count
            annotated_qs = qs.values(field_name).annotate(
                vote_count=models.Count(1)
            )

            # If tie_break_field is provided, order by it after vote_count
            if tie_break_field:
                annotated_qs = annotated_qs.order_by('-vote_count', tie_break_field)
            else:
                annotated_qs = annotated_qs.order_by('-vote_count')

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
        experts_annotations_qs = self.expert_report_annotations.filter(user__groups__name='expert').exclude(user__groups__name='superexpert')
        finished_experts_annotations_qs = experts_annotations_qs.filter(validation_complete=True)

        # Find executive and superexpert annotations
        executive_annotation = finished_experts_annotations_qs.filter(validation_complete_executive=True).order_by('-last_modified').first()
        superexpert_annotation = self.expert_report_annotations.filter(validation_complete=True, user__groups__name='superexpert').order_by('-revise', '-last_modified').first()

        # Update task statistics
        self.total_annotations = experts_annotations_qs.count()
        self.total_finished_annotations = finished_experts_annotations_qs.count()

        current_photo_id = self.photo_id
        if superexpert_annotation and superexpert_annotation.revise:
            # Case 1: Superexpert revision (overwrite)
            self._update_from_annotation(
                annotation=superexpert_annotation,
                default_status=self.Status.DONE
            )
        elif not self.is_reviewed or force:
            # TODO: ensure annotations are before superexpert revision -> pending, there are annotations that not meet this requirement.
            if executive_annotation:
                # Case 2: Executive validation
                default_status = (
                    self.Status.FLAGGED if executive_annotation.status == ExpertReportAnnotation.STATUS_FLAGGED 
                    else self.Status.DONE
                )
                self._update_from_annotation(
                    annotation=executive_annotation,
                    default_status=default_status
                )
            elif self.total_finished_annotations >= settings.MAX_N_OF_EXPERTS_ASSIGNED_PER_REPORT:
                # Case 3: Sufficient annotations for final decision
                taxon, confidence, uncertainty, agreement = self.get_taxon_consensus(
                    annotations=list(finished_experts_annotations_qs)
                )
                if uncertainty > 0.92:
                    self.taxon = Taxon.get_root()
                    self.confidence = Decimal('1.0')
                    self.uncertainty = 1.0
                    self.agreement = 0.0
                    self.status = self.Status.CONFLICT
                else:
                    self.taxon = taxon
                    self.confidence = confidence
                    self.uncertainty = uncertainty
                    self.agreement = agreement

                    if finished_experts_annotations_qs.filter(status=ExpertReportAnnotation.STATUS_FLAGGED).exists():
                        self.status = self.Status.FLAGGED
                    elif self.agreement == 0 and finished_experts_annotations_qs.filter(taxon__is_relevant=True).exists():
                        # All experts has choosen different things.
                        self.status = self.Status.CONFLICT
                    else:
                        self.status = self.Status.REVIEW

                if self.taxon:
                    taxon_filter = {
                        'taxon__in': Taxon.get_tree(parent=self.taxon)
                    }
                else:
                    taxon_filter = {
                        'taxon__isnull': True
                    }
                self.photo_id = get_most_voted_field(field_name='best_photo', lookup_filter=taxon_filter)
                self.public_note = get_most_voted_field(field_name='edited_user_notes', lookup_filter=taxon_filter)
                self.is_safe = get_most_voted_field(field_name='status') == ExpertReportAnnotation.STATUS_PUBLIC
            elif self.total_finished_annotations < self.total_annotations:
                # Check for flagged annotations
                if finished_experts_annotations_qs.filter(status=ExpertReportAnnotation.STATUS_FLAGGED).exists():
                    self.status = self.Status.FLAGGED
            else:
                # Back to defaults. e.g: when ExpertReportAnnotation delete
                self.status = self._meta.get_field('status').default
                self.public_note = None
                self.message_for_user = None
                self.taxon = None
                self.confidence = self._meta.get_field('confidence').default
                self.uncertainty = self._meta.get_field('uncertainty').default
                self.agreement = self._meta.get_field('agreement').default
                self.is_safe = self._meta.get_field('is_safe').default

        # Ensure photo_id is updated and save the instance
        self.photo_id = self.photo_id or current_photo_id

        if superexpert_annotation:
            self.reviewed_at = superexpert_annotation.last_modified
            self.revision_type = self.Revision.OVERWRITE if superexpert_annotation.revise else self.Revision.AGREE
        else:
            self.reviewed_at = None
            self.revision_type = None

        if self.is_reviewed:
            self.status = self.Status.DONE

        if self.report.deleted or self.report.hide or self.report.tags.filter(name='345').exists():
            self.status = self.Status.ARCHIVED

        if commit:
            # Save the updated instance
            # NOTE: do not force saving only certain fields, as it may cause inconsistencies.
            self.save()

    @hook(
        AFTER_SAVE,
        condition=WhenFieldValueChangesTo(
            'status',
            value=Status.DONE
        ),
    )
    def on_done(self) -> None:
        from .messaging import send_finished_identification_task_notification
        send_finished_identification_task_notification(
            identification_task=self,
            from_user=User.objects.filter(pk=25).first()
        )

    def save(self, *args, **kwargs):
        if self.report.deleted or self.report.hide:
            self.status = self.Status.ARCHIVED

        return super().save(*args, **kwargs)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(total_finished_annotations__lte=models.F('total_annotations')),
                name='total_finished_annotations_lte_total_annotations'
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
            )
        ]


class Annotation(models.Model):
    user = models.ForeignKey('auth.User', related_name='annotations', on_delete=models.PROTECT, )
    task = models.ForeignKey('tigacrafting.CrowdcraftingTask', related_name='annotations', on_delete=models.CASCADE, )
    tiger_certainty_percent = models.IntegerField('Degree of belief',validators=[MinValueValidator(0), MaxValueValidator(100)], blank=True, null=True)
    value_changed = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    last_modified = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    working_on = models.BooleanField(default=False)

    def __unicode__(self):
        return "Annotation: " + str(self.id) + ", Task: " + str(self.task.task_id)


class MoveLabAnnotation(models.Model):
    task = models.OneToOneField(CrowdcraftingTask, related_name='movelab_annotation', on_delete=models.CASCADE, )
    CATEGORIES = ((-2, 'Definitely not a tiger mosquito'), (-1, 'Probably not a tiger mosquito'), (0, 'Not sure'), (1, 'Probably a tiger mosquito'), (2, 'Definitely a tiger mosquito'))
    tiger_certainty_category = models.IntegerField('Certainty', choices=CATEGORIES, blank=True, null=True)
    certainty_notes = models.TextField(blank=True)
    hide = models.BooleanField('Hide photo from public', default=False)
    edited_user_notes = models.TextField(blank=True)
    last_modified = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

TIGER_CATEGORIES = ((2, 'Definitely Aedes albopictus'), (1, 'Probably Aedes albopictus'),  (0, 'Not sure'), (-1, 'Probably neither albopictus nor aegypti'), (-2, 'Definitely not albopictus or aegypti'))

#WARNING!! THIS IS USED FOR VISUALIZATION ONLY, NEVER SHOULD BE USED FOR DATA INPUT!!!
TIGER_CATEGORIES_SEPARATED = ((2, 'Definitely Aedes albopictus'), (1, 'Probably Aedes albopictus'),  (0, 'Not sure'), (-1, 'Probably not albopictus'), (-2, 'Definitely not albopictus'))

AEGYPTI_CATEGORIES = ((2, 'Definitely Aedes aegypti'), (1, 'Probably Aedes aegypti'),  (0, 'Not sure'), (-1, 'Probably neither albopictus nor aegypti'), (-2, 'Definitely not albopictus or aegypti'))

#WARNING!! THIS IS USED FOR VISUALIZATION ONLY, NEVER SHOULD BE USED FOR DATA INPUT!!!
AEGYPTI_CATEGORIES_SEPARATED = ((2, 'Definitely Aedes aegypti'), (1, 'Probably Aedes aegypti'),  (0, 'Not sure'), (-1, 'Probably not aegypti'), (-2, 'Definitely not aegypti'))

SITE_CATEGORIES = ((2, 'Definitely a breeding site'), (1, 'Probably a breeding site'), (0, 'Not sure'), (-1, 'Probably not a breeding site'), (-2, 'Definitely not a breeding site'))

class ExpertReportAnnotation(models.Model):
    VALIDATION_CATEGORY_DEFINITELY = 2
    VALIDATION_CATEGORY_PROBABLY = 1
    VALIDATION_CATEGORIES = ((VALIDATION_CATEGORY_DEFINITELY, 'Definitely'), (VALIDATION_CATEGORY_PROBABLY, 'Probably'))

    STATUS_HIDDEN = -1
    STATUS_FLAGGED = 0
    STATUS_PUBLIC = 1
    STATUS_CATEGORIES = ((STATUS_PUBLIC, 'public'), (STATUS_FLAGGED, 'flagged'), (STATUS_HIDDEN, 'hidden'))

    user = models.ForeignKey(User, related_name="expert_report_annotations", on_delete=models.PROTECT, )
    report = models.ForeignKey('tigaserver_app.Report', related_name='expert_report_annotations', on_delete=models.CASCADE, )
    # NOTE: identification_task is nullable due to legacy. There are annotations to sites.
    identification_task = models.ForeignKey(IdentificationTask, null=True, blank=True, editable=False, related_name='expert_report_annotations', on_delete=models.CASCADE)
    tiger_certainty_category = models.IntegerField('Tiger Certainty', choices=TIGER_CATEGORIES, default=None, blank=True, null=True, help_text='Your degree of belief that at least one photo shows a tiger mosquito')
    aegypti_certainty_category = models.IntegerField('Aegypti Certainty', choices=AEGYPTI_CATEGORIES, default=None, blank=True, null=True, help_text='Your degree of belief that at least one photo shows an Aedes aegypti')
    tiger_certainty_notes = models.TextField('Internal Species Certainty Comments', blank=True, help_text='Internal notes for yourself or other experts')
    site_certainty_category = models.IntegerField('Site Certainty', choices=SITE_CATEGORIES, default=None, blank=True, null=True, help_text='Your degree of belief that at least one photo shows a tiger mosquito breeding site')
    site_certainty_notes = models.TextField('Internal Site Certainty Comments', blank=True, help_text='Internal notes for yourself or other experts')
    edited_user_notes = models.TextField('Public Note', blank=True, help_text='Notes to display on public map')
    message_for_user = models.TextField('Message to User', blank=True, help_text='Message that user will receive when viewing report on phone')
    status = models.IntegerField('Status', choices=STATUS_CATEGORIES, default=1, help_text='Whether report should be displayed on public map, flagged for further checking before public display), or hidden.')
    #last_modified = models.DateTimeField(auto_now=True, default=datetime.now())
    last_modified = models.DateTimeField(default=timezone.now)
    validation_complete = models.BooleanField(default=False, db_index=True, help_text='Mark this when you have completed your review and are ready for your annotation to be displayed to public.')
    revise = models.BooleanField(default=False, help_text='For superexperts: Mark this if you want to substitute your annotation for the existing Expert annotations. Make sure to also complete your annotation form and then mark the "validation complete" box.')
    best_photo = models.ForeignKey('tigaserver_app.Photo', related_name='expert_report_annotations', null=True, blank=True, on_delete=models.SET_NULL, )
    linked_id = models.CharField('Linked ID', max_length=10, help_text='Use this field to add any other ID that you want to associate the record with (e.g., from some other database).', blank=True)
    created = models.DateTimeField(auto_now_add=True)
    simplified_annotation = models.BooleanField(default=False, help_text='If True, the report annotation interface shows less input controls')
    tags = TaggableManager(blank=True)
    category = models.ForeignKey('tigacrafting.Categories', related_name='expert_report_annotations', null=True, blank=True, help_text='Simple category assigned by expert or superexpert. Mutually exclusive with complex. If this field has value, then probably there is a validation value', on_delete=models.SET_NULL, )
    complex = models.ForeignKey('tigacrafting.Complex', related_name='expert_report_annotations', null=True, blank=True, help_text='Complex category assigned by expert or superexpert. Mutually exclusive with category. If this field has value, there should not be a validation value', on_delete=models.SET_NULL, )
    validation_value = models.IntegerField('Validation Certainty', choices=VALIDATION_CATEGORIES, default=None, blank=True, null=True, help_text='Certainty value, 1 for probable, 2 for sure, 0 for none')
    other_species = models.ForeignKey('tigacrafting.OtherSpecies', related_name='expert_report_annotations', null=True, blank=True, help_text='Additional info supplied if the user selected the Other species category', on_delete=models.SET_NULL, )
    validation_complete_executive = models.BooleanField(default=False, db_index=True, help_text='Available only to national supervisor. Causes the report to be completely validated, with the final classification decided by the national supervisor')

    taxon = models.ForeignKey('tigacrafting.Taxon', null=True, blank=True, on_delete=models.PROTECT)
    confidence = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])

    objects = ExpertReportAnnotationManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'report'], name='unique_assignation'),
            models.CheckConstraint(
                check=models.Q(confidence__gte=0) & models.Q(confidence__lte=1),
                name='expertreportannotation_confidence_between_0_and_1'
            )
        ]

    def is_superexpert(self):
        return self.user.groups.filter(name='superexpert').exists()

    def is_expert(self):
        return self.user.groups.filter(name='expert').exists()

    @property
    def is_on_ns_executive_validation_period(self):
        if not self.identification_task:
            return False
        return self.identification_task.in_exclusivity_period

    @property
    def confidence_label(self):
        return get_confidence_label(value=self.confidence)

    @classmethod
    def _get_auto_message(cls, category: 'Categories', validation_value: int, locale: str = 'en') -> Optional[str]:
        msg_dict = other_insect_msg_dict
        if not category:
            return msg_dict.get(locale)

        if category.pk == 4:  # albopictus
            msg_dict = albopictus_msg_dict if validation_value == cls.VALIDATION_CATEGORY_DEFINITELY else albopictus_probably_msg_dict
        elif category.pk == 10:  # culex
            msg_dict = culex_msg_dict
        elif category.pk == 9:  # not sure
            msg_dict = notsure_msg_dict

        return msg_dict.get(locale)

    @classmethod
    def create_auto_annotation(cls, report: 'tigaserver_app.models.Report', category: 'Categories', validation_value: Optional[Literal[VALIDATION_CATEGORY_PROBABLY, VALIDATION_CATEGORY_DEFINITELY]] = None):
        obj, _ = ExpertReportAnnotation.objects.update_or_create(
            user=User.objects.get(username="innie"),
            report=report,
            defaults={
                'validation_complete': True,
                'simplified_annotation': False,
                'best_photo': report.photos.first(),
                'category': category,
                'tiger_certainty_notes': 'auto',
                'validation_value': int(validation_value) if validation_value else None,
                'edited_user_notes': cls._get_auto_message(
                    category=category,
                    validation_value=int(validation_value) if validation_value else None,
                    locale=report.user.locale
                ) or ""
            }
        )
        obj.create_replicas()
        cls.create_super_expert_approval(report=report)

    @classmethod
    def create_super_expert_approval(cls, report: 'tigaserver_app.models.Report'):
        from tigaserver_app.models import Report

        if report.type == Report.TYPE_ADULT:
            # TODO: at some point, superexpert should not auto-review. Remove all
            #       annotations from superexpert that are revise=False and are in
            #       a ExpertReportAnnotation that are replicas or executive validation.
            ExpertReportAnnotation.objects.update_or_create(
                user=User.objects.get(pk=25),  # "super_reritja"
                report=report,
                defaults={
                    'status': 1,  # public
                    'simplified_annotation': False,
                    'revise': False,
                    'validation_complete': True,
                }
            )
        elif report.type == Report.TYPE_SITE:
            ExpertReportAnnotation.objects.update_or_create(
                user=User.objects.get(pk=24),  # "super_movelab"
                report=report,
                defaults={
                    'best_photo': report.photos.first(),
                    'site_certainty_notes': 'auto',
                    'status': 1,  # public
                    'simplified_annotation': False,
                    'revise': True,
                    'validation_complete': True,
                }
            )

    def create_replicas(self):
        username_replicas = ["innie", "minnie", "manny"]

        report_annotations = ExpertReportAnnotation.objects.filter(report=self.report).count()
        if report_annotations >= settings.MAX_N_OF_EXPERTS_ASSIGNED_PER_REPORT:
            return
        num_missing_annotations = settings.MAX_N_OF_EXPERTS_ASSIGNED_PER_REPORT - report_annotations

        fieldnames = [
            field.name for field in ExpertReportAnnotation._meta.fields if field.name not in ('id', 'user', 'report')
        ]
        obj_dict = {
            fname: getattr(self, fname) for fname in fieldnames
        }
        for dummy_user in User.objects.filter(username__in=username_replicas).exclude(username=self.user.username)[:num_missing_annotations]:
            ExpertReportAnnotation.objects.update_or_create(
                user=dummy_user,
                report=self.report,
                defaults={
                    **obj_dict,
                    'tiger_certainty_category': self.tiger_certainty_category,
                    'simplified_annotation': True,
                    'tiger_certainty_notes': 'exec_auto' if self.validation_complete_executive else 'auto',
                    'validation_complete': True,
                    'validation_complete_executive': False,
                    'best_photo': None,
                    'edited_user_notes': "",
                    'message_for_user': "",
                    'revise': False
                }
            )

    # def get_photo_html_for_report_validation_wblood(self):
    #     #these_photos = Photo.objects.filter(report=self.report).visible()
    #     these_photos = self.report.photos.all()
    #     result = ''
    #     for photo in these_photos:
    #         male_status = 'checked="checked"' if photo.blood_genre == 'male' else ''
    #         female_status = 'checked="checked"' if photo.blood_genre == 'female' else ''
    #         fblood_status = 'checked="checked"' if photo.blood_genre == 'fblood' else ''
    #         #dk_status = 'checked="checked"' if photo.blood_genre == 'dk' else ''
    #         fg_status = 'checked="checked"' if photo.blood_genre == 'fgravid' else ''
    #         fgb_status = 'checked="checked"' if photo.blood_genre == 'fgblood' else ''
    #         result += '<div data-ano-id="' + str(self.id) + '" id="div_for_photo_to_display_report_' + str(self.report.version_UUID) + '">' \
    #                     '<input type="radio" name="photo_to_display_report_' + str(self.report.version_UUID) + '" id="' + str(photo.id) + '" value="' + str(photo.id) + '"/>Display this photo on public map:' \
    #                 '</div>' \
    #                 '<br>' \
    #                 '<div style="border: 1px solid #333333;margin:1px;">' + photo.medium_image_for_validation_() + '</div>' \
    #                 '<br>' \
    #                '<div id="blood_status_' + str(self.report.version_UUID) + '_' + str(photo.id) + '">' \
    #                '<label title="Male" class="radio-inline"><input type="radio" value="' + str(photo.id) + '_male" name="fblood_' + str(photo.id) + '" ' + male_status + '><i class="fa fa-mars fa-lg" aria-hidden="true"></i></label>' \
    #                '<label title="Female" class="radio-inline"><input type="radio" value="' + str(photo.id) + '_female" name="fblood_' + str(photo.id) + '" ' + female_status + '><i class="fa fa-venus fa-lg" aria-hidden="true"></i></label>' \
    #                '<label title="Female blood" class="radio-inline"><input value="' + str(photo.id) + '_fblood" type="radio" name="fblood_' + str(photo.id) + '" ' + fblood_status + '><i class="fa fa-tint fa-lg" aria-hidden="true"></i></label>' \
    #                '<label title="Female gravid" class="radio-inline"><input type="radio" value="' + str(photo.id) + '_fgravid" name="fblood_' + str(photo.id) + '" ' + fg_status + '><i class="moon" aria-hidden="true"></i></label>' \
    #                '<label title="Female gravid + blood" class="radio-inline"><input type="radio" value="' + str(photo.id) + '_fgblood" name="fblood_' + str(photo.id) + '" ' + fgb_status + '><i class="moon" aria-hidden="true"></i><i class="fa fa-plus fa-lg" aria-hidden="true"></i><i class="fa fa-tint fa-lg" aria-hidden="true"></i></label>' \
    #                '</div>' \
    #
    #     return result

    def get_photo_html_for_report_validation_wblood(self):
        # these_photos = Photo.objects.filter(report=self.report).visible()
        these_photos = self.report.photos.all()
        result = ''
        for photo in these_photos:
            male_status = 'checked="checked"' if photo.blood_genre == 'male' else ''
            female_status = 'checked="checked"' if photo.blood_genre == 'female' else ''
            fblood_status = 'checked="checked"' if photo.blood_genre == 'fblood' else ''
            dk_status = 'checked="checked"' if photo.blood_genre == 'dk' else ''
            fg_status = 'checked="checked"' if photo.blood_genre == 'fgravid' else ''
            fgb_status = 'checked="checked"' if photo.blood_genre == 'fgblood' else ''
            result += '<div class="rb_display_this_photo" data-ano-id="' + str(self.id) + '" id="div_for_photo_to_display_report_' + str(self.report.version_UUID) + '">' \
                        '<input type="radio" name="photo_to_display_report_' + str(self.report.version_UUID) + '" id="' + str(photo.id) + '" value="' + str(photo.id) + '"/>Display this photo on public map:' \
                    '</div>' \
                    '<br>' \
                    '<div style="border: 1px solid #333333;margin:1px;">' + photo.medium_image_for_validation_() + '</div>' \
                    '<br>' \
                   '<div id="blood_status_' + str(self.report.version_UUID) + '_' + str(photo.id) + '">' \
                   '<label title="Male" class="radio-inline"><input type="radio" value="' + str(photo.id) + '_male" name="fblood_' + str(photo.id) + '" ' + male_status + '><i class="fa fa-mars fa-lg" aria-hidden="true"></i></label>' \
                   '<label title="Female" class="radio-inline"><input type="radio" value="' + str(photo.id) + '_female" name="fblood_' + str(photo.id) + '" ' + female_status + '><i class="fa fa-venus fa-lg" aria-hidden="true"></i></label>' \
                   '<label title="Female blood" class="radio-inline"><input value="' + str(photo.id) + '_fblood" type="radio" name="fblood_' + str(photo.id) + '" ' + fblood_status + '><i class="fa fa-tint fa-lg" aria-hidden="true"></i></label>' \
                   '<label title="Female gravid" class="radio-inline"><input type="radio" value="' + str(photo.id) + '_fgravid" name="fblood_' + str(photo.id) + '" ' + fg_status + '><i class="fa fa-dot-circle-o fa-lg" aria-hidden="true"></i></label>' \
                   '<label title="Female gravid + blood" class="radio-inline"><input type="radio" value="' + str(photo.id) + '_fgblood" name="fblood_' + str(photo.id) + '" ' + fgb_status + '><i class="fa fa-dot-circle-o fa-lg" aria-hidden="true"></i><i class="fa fa-plus fa-lg" aria-hidden="true"></i><i class="fa fa-tint fa-lg" aria-hidden="true"></i></label>' \
                   '<label title="Dont know" class="radio-inline"><input type="radio" value ="' + str(photo.id) + '_dk" name="fblood_' + str(photo.id) + '" ' + dk_status + '><i class="fa fa-question fa-lg" aria-hidden="true"></i></label>' \
                   '</div>'
        return result


    def get_photo_html_for_report_validation(self):
        #these_photos = Photo.objects.filter(report__version_UUID=self.version_UUID).visible()
        these_photos = self.report.photos.all()
        result = ''
        for photo in these_photos:
            result += '<div data-ano-id="' + str(self.id) + '" id="div_for_photo_to_display_report_' + str(self.report.version_UUID) + '">' \
                    '<input type="radio" name="photo_to_display_report_' + str(self.report.version_UUID) + '" id="' + str(photo.id) + '" value="' + str(photo.id) + '"/>Display this photo on public map:' \
                    '</div>' \
                    '<br>' \
                    '<div style="border: 1px solid #333333;margin:1px;">' + photo.medium_image_for_validation_() + '</div>' \
                    '<br>'
        return result

    def get_photo_html_for_report_validation_superexpert(self):
        #these_photos = Photo.objects.filter(report__version_UUID=self.version_UUID).visible()
        these_photos = self.report.photos.all()
        result = ''

        for photo in these_photos:
            best_photo = ExpertReportAnnotation.objects.filter(best_photo=photo).exists()
            border_style = "3px solid green" if best_photo else "1px solid #333333"
            male_status = 'checked="checked"' if photo.blood_genre == 'male' else ''
            female_status = 'checked="checked"' if photo.blood_genre == 'female' else ''
            fblood_status = 'checked="checked"' if photo.blood_genre == 'fblood' else ''
            #dk_status = 'checked="checked"' if photo.blood_genre == 'dk' else ''
            fg_status = 'checked="checked"' if photo.blood_genre == 'fgravid' else ''
            fgb_status = 'checked="checked"' if photo.blood_genre == 'fgblood' else ''
            result += '<div data-ano-id="' + str(self.id) + '" id="div_for_photo_to_display_report_' + str(self.report.version_UUID) + '">' \
                        '<input data-best="' + str(best_photo) + '" type="radio" name="photo_to_display_report_' + str(self.report.version_UUID) + '" id="' + str(photo.id) + '" value="' + str(photo.id) + '"/>Display this photo on public map:'\
                        '</div>' \
                        '<br>' \
                        '<div style="border:' + border_style + ';margin:1px;position: relative;">' + photo.medium_image_for_validation_() + '</div>'
                        # '<div id="blood_status_' + str(self.report.version_UUID) + '_' + str(photo.id) + '">' \
                        # '<label title="Male" class="radio-inline"><input type="radio" value="' + str(photo.id) + '_male" name="fblood_' + str(photo.id) + '" ' + male_status + '><i class="fa fa-mars fa-lg" aria-hidden="true"></i></label>' \
                        # '<label title="Female" class="radio-inline"><input type="radio" value="' + str(photo.id) + '_female" name="fblood_' + str(photo.id) + '" ' + female_status + '><i class="fa fa-venus fa-lg" aria-hidden="true"></i></label>' \
                        # '<label title="Female blood" class="radio-inline"><input value="' + str(photo.id) + '_fblood" type="radio" name="fblood_' + str(photo.id) + '" ' + fblood_status + '><i class="fa fa-tint fa-lg" aria-hidden="true"></i></label>' \
                        # '<label title="Female gravid" class="radio-inline"><input type="radio" value="' + str(photo.id) + '_fgravid" name="fblood_' + str(photo.id) + '" ' + fg_status + '><i class="moon" aria-hidden="true"></i></label>' \
                        # '<label title="Female gravid + blood" class="radio-inline"><input type="radio" value="' + str(photo.id) + '_fgblood" name="fblood_' + str(photo.id) + '" ' + fgb_status + '><i class="moon" aria-hidden="true"></i><i class="fa fa-plus fa-lg" aria-hidden="true"></i><i class="fa fa-tint fa-lg" aria-hidden="true"></i></label>' \
                        # '</div>' \
                        # '<br>'
        return result

    def get_others_annotation_html(self):
        result = ''
        this_user = self.user
        this_report = self.report
        other_annotations = ExpertReportAnnotation.objects.filter(report=this_report).exclude(user=this_user)
        for ano in other_annotations.all():
            result += '<p>User: ' + ano.user.username + '</p>'
            result += '<p>Last Edited: ' + ano.last_modified.strftime("%d %b %Y %H:%m") + ' UTC</p>'
            if this_report.type == 'adult':
                result += '<p>Tiger Certainty: ' + (ano.get_tiger_certainty_category_display() if ano.get_tiger_certainty_category_display() else "") + '</p>'
                result += '<p>Tiger Notes: ' + ano.tiger_certainty_notes + '</p>'
            elif this_report.type == 'site':
                result += '<p>Site Certainty: ' + (ano.get_site_certainty_category_display() if ano.get_site_certainty_category_display() else "") + '</p>'
                result += '<p>Site Notes: ' + ano.site_certainty_notes + '</p>'
            result += '<p>Selected photo: ' + (ano.best_photo.popup_image() if ano.best_photo else "") + '</p>'
            result += '<p>Edited User Notes: ' + ano.edited_user_notes + '</p>'
            result += '<p>Message To User: ' + ano.message_for_user + '</p>'
            result += '<p>Status: ' + ano.get_status_display() if ano.get_status_display() else "" + '</p>'
            result += '<p>Validation Complete? ' + str(ano.validation_complete) + '</p><hr>'
        return result

    def get_score(self):
        score = -3
        if self.report.type == 'site':
            score = self.site_certainty_category
        elif self.report.type == 'adult':
            if self.aegypti_certainty_category == 2:
                score = 4
            elif self.aegypti_certainty_category == 1:
                score = 3
            else:
                score = self.tiger_certainty_category
        if score is not None:
            return score
        else:
            return -3

    def get_html_color_for_label(self) -> str:
        return html_utils.get_html_color_for_label(
            taxon=self.taxon,
            confidence=self.confidence
        )

    def get_category_euro(self) -> str:
        if self.report.type == 'site':
            return dict([(-3, 'Unclassified')] + list(SITE_CATEGORIES))[self.get_score()]
        elif self.report.type == 'adult':
            if not self.taxon:
                return "Not sure"
            if self.taxon.is_relevant:
                return self.taxon.name
            return "Other species - " + self.taxon.name

    def get_category(self) -> str:
        if self.report.type == 'site':
            return dict([(-3, 'Unclassified')] + list(SITE_CATEGORIES))[self.get_score()]
        elif self.report.type == 'adult':
            if self.get_score() > 2:
                return dict([(-3, 'Unclassified')] + list(AEGYPTI_CATEGORIES))[self.get_score()-2]
            else:
                return dict([(-3, 'Unclassified')] + list(TIGER_CATEGORIES))[self.get_score()]

    def get_status_bootstrap(self):
        result = '<span data-toggle="tooltip" data-placement="bottom" title="' + self.get_status_display() + '" class="' + ('glyphicon glyphicon-eye-open' if self.status == 1 else ('glyphicon glyphicon-flag' if self.status == 0 else 'glyphicon glyphicon-eye-close')) + '"></span>'
        return result

    def get_score_bootstrap(self):
        result = '<span class="label label-default" style="background-color:' + ('red' if self.get_score() == 2 else ('orange' if self.get_score() == 1 else ('white' if self.get_score() == 0 else ('grey' if self.get_score() == -1 else 'black')))) + ';">' + self.get_category() + '</span>'
        return result

    def _get_confidence(self) -> float:
        if self.validation_value == self.VALIDATION_CATEGORY_DEFINITELY:
            return 1.0
        elif self.validation_value == self.VALIDATION_CATEGORY_PROBABLY:
            return 0.75
        else:
            if taxon := self._get_taxon():
                return 1.0 if taxon.rank < Taxon.TaxonomicRank.SPECIES_COMPLEX else 0.75

            return 0.0

    def _get_taxon(self) -> Optional['Taxon']:
        if self.complex:
            return self.complex.taxa.first()

        if self.other_species:
            return self.other_species.taxa.first()

        if self.category:
            if self.category.pk == 1:   # Case Unclassified.
                return None
            elif self.category.pk == 9: # Case 'Not sure'
                return None
            elif self.category.pk == 2: # Case "Other species" selected
                return Taxon.get_root()
            else:
                return self.category.taxa.first()

        return None

    def _can_be_simplified(self) -> bool:
        # If the user is the superexpert -> False
        if self.user.userstat.is_superexpert():
            return False

        # If the user is the supervisor of that country -> False
        if self.user.userstat.national_supervisor_of:
            if self.user.userstat.national_supervisor_of == self.report.country:
                return False

        # Return False if no simplified_annotation found or if the objects to be
        # created is suposed to be the last.
        total_completed_annotations_qs = self.report.expert_report_annotations.all()
        return (
            total_completed_annotations_qs.filter(simplified_annotation=False).exists() or
            total_completed_annotations_qs.count() < settings.MAX_N_OF_EXPERTS_ASSIGNED_PER_REPORT - 1
        )

    def save(self, *args, **kwargs):
        if not kwargs.pop('skip_lastmodified', False):
            self.last_modified = timezone.now()

        if self.category:
            self.tiger_certainty_category = -2
            if self.category.pk == 4: # albopictus
                self.tiger_certainty_category = 2

            self.aegypti_certainty_category = -2
            if self.category.pk == 5: # aegypti
                self.aegypti_certainty_category = 2

        # On create only
        if self._state.adding:
            _userstat = self.user.userstat
            _userstat.grabbed_reports += 1
            _userstat.save()
            if not self.validation_complete:
                self.simplified_annotation = self._can_be_simplified()

        if self.simplified_annotation:
            self.message_for_user = ""
            self.best_photo = None

        if not self.identification_task or str(self.identification_task.pk) != str(self.report.pk):
            self.identification_task = IdentificationTask.objects.filter(report=self.report).first()
        self.taxon = self._get_taxon()
        self.confidence = self._get_confidence()

        super(ExpertReportAnnotation, self).save(*args, **kwargs)

        if self.validation_complete and self.validation_complete_executive:
            self.create_replicas()
            self.create_super_expert_approval(report=self.report)

        if self.identification_task:
            self.identification_task.refresh()

    def delete(self, *args, **kwargs):
        if self.validation_complete_executive:
            ExpertReportAnnotation.objects.filter(
                report=self.report,
                validation_complete=True,
                validation_complete_executive=False
            ).filter(
                models.Q(user__username__in=["innie", "minnie"]) 
                | models.Q(user__pk=25, revise=False)   # pk 25 = "super_reritja"
            ).delete()

        identification_task = self.identification_task

        result = super().delete(*args, **kwargs)

        if identification_task:
            identification_task.refresh(force=True)

        return result

class UserStat(models.Model):
    user = models.OneToOneField(User, primary_key=True, on_delete=models.CASCADE, )
    grabbed_reports = models.IntegerField('Grabbed reports', default=0, help_text='Number of reports grabbed since implementation of simplified reports. For each 3 reports grabbed, one is simplified')
    national_supervisor_of = models.ForeignKey('tigaserver_app.EuropeCountry', blank=True, null=True, related_name="supervisors", help_text='Country of which the user is national supervisor. It means that the user will receive all the reports in his country', on_delete=models.PROTECT, )
    native_of = models.ForeignKey('tigaserver_app.EuropeCountry', blank=True, null=True, related_name="natives", help_text='Country in which the user operates. Used mainly for filtering purposes', on_delete=models.SET_NULL, )
    license_accepted = models.BooleanField('Value is true if user has accepted the license terms of EntoLab', default=False)
    # When in crisis mode, several regional restrictions are disabled and the user preferently receives reports
    # from places where there has been a spike
    crisis_mode = models.BooleanField('Tells if the validator is working in crisis mode or not', default=False)
    last_emergency_mode_grab = models.ForeignKey('tigaserver_app.EuropeCountry', blank=True, null=True,related_name="emergency_pullers", help_text='Last country user pulled map data from', on_delete=models.SET_NULL, )
    nuts2_assignation = models.ForeignKey('tigaserver_app.NutsEurope', blank=True, null=True, related_name="nuts2_assigned", help_text='Nuts2 division in which the user operates. Influences the priority of report assignation', on_delete=models.SET_NULL, )

    def __str__(self):
        geo_label = ''
        if self.native_of:
            geo_label = self.native_of.name_engl
        if self.nuts2_assignation:
            geo_label += "{0} ({1})".format(self.nuts2_assignation.europecountry.name_engl, self.nuts2_assignation.name_latn)
        return f"{self.user.username} - {geo_label}"

    @property
    def completed_annotations(self):
        return self.user.expert_report_annotations.filter(validation_complete=True)

    @property
    def num_completed_annotations(self) -> int:
        return self.completed_annotations.count()

    @property
    def pending_annotations(self):
        return self.user.expert_report_annotations.filter(validation_complete=False)

    @property
    def num_pending_annotations(self) -> int:
        return self.pending_annotations.count()

    @transaction.atomic
    def assign_reports(self, country: Optional['EuropeCountry'] = None) -> List[Optional[IdentificationTask]]:
        task_queue = IdentificationTask.objects.exclude(assignees=self.user).select_related('report')
        if country is not None:
            task_queue = task_queue.filter(report__country=country)

        if self.is_superexpert():
            task_queue = task_queue.to_review().order_by('created_at')
        else:
            task_queue = task_queue.backlog(user=self.user)
            # Only assign until reaching the maximum allowed.
            current_pending = self.num_pending_annotations
            if current_pending >= settings.MAX_N_OF_PENDING_REPORTS:
                return

            num_to_assign = settings.MAX_N_OF_PENDING_REPORTS - current_pending
            task_queue = task_queue.all()[:num_to_assign]

        result = []
        for task in task_queue:
            task.assign_to_user(user=self.user)
            result.append(task)

        return result

    def assign_crisis_report(self, country: 'EuropeCountry') -> List[Optional[IdentificationTask]]:
        # NOTE: self.save() is called in assign_reports
        self.last_emergency_mode_grab = country
        return self.assign_reports(country=country)

    def has_accepted_license(self):
        return self.license_accepted

    def is_expert(self):
        return self.user.groups.filter(name="expert").exists()

    def is_superexpert(self):
        return self.user.groups.filter(name="superexpert").exists()

    def is_movelab(self):
        return self.user.groups.filter(name="movelab").exists()

    def is_team_bcn(self):
        return self.user.groups.filter(name="team_bcn").exists()

    def is_team_not_bcn(self):
        return self.user.groups.filter(name="team_not_bcn").exists()

    def is_team_everywhere(self):
        return self.user.groups.exclude(name="team_not_bcn").exclude(name="team_bcn").exists()

    def is_bb_user(self):
        if self.native_of is not None:
            return self.native_of.is_bounding_box
        return False

    # only regular users can activate crisis mode
    def can_activate_crisis_mode(self):
        if self.is_superexpert():
            return False
        if self.is_bb_user():
            return False
        if self.is_national_supervisor():
            return False
        return True

    def is_national_supervisor(self):
        return self.national_supervisor_of is not None

    def is_national_supervisor_for_country(self, country):
        return self.is_national_supervisor() and self.national_supervisor_of.gid == country.gid
    
    @property
    def formatted_country_info(self):
        this_user = self.user
        this_user_is_team_bcn = this_user.groups.filter(name='team_bcn').exists()
        this_user_is_team_not_bcn = this_user.groups.filter(name='team_not_bcn').exists()
        this_user_is_europe = this_user.groups.filter(name='eu_group_europe').exists()
        this_user_is_team_everywhere = self.is_team_everywhere()
        this_user_is_spain = not this_user_is_europe
        if this_user_is_spain:
            if this_user_is_team_bcn:
                return "Spain - Barcelona"
            elif this_user_is_team_not_bcn:
                return "Spain - Outside Barcelona"
            else:
                return "Spain - Global"
        else:
            if self.is_national_supervisor():
                return "Europe - National supervisor - " + self.national_supervisor_of.name_engl
            else:
                return "Europe - " + self.native_of.name_engl


    # this method returns the username, changing any '.' character to a '_'. This is used to avoid usernames used
    # as id or class names in views to break jquery selector queries
    @property
    def username_nopoint(self):
        return self.user.username.replace('.', '_')

    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            UserStat.objects.create(user=instance)

    @receiver(post_save, sender=User)
    def save_user_profile(sender, instance, **kwargs):
        try:
            instance.userstat.save()
        except UserStat.DoesNotExist:
            UserStat.objects.create(user=instance)

class Categories(models.Model):
    name = models.TextField('Name of the classification category', help_text='Usually a species category. Can also be other/special case values')
    specify_certainty_level = models.BooleanField(default=False, help_text='Indicates if for this row a certainty level must be supplied')

    taxa = GenericRelation('tigacrafting.Taxon')

    def __str__(self):
        return self.name


class Complex(models.Model):
    description = models.TextField('Name of the complex category', help_text='This table is reserved for species combinations')

    taxa = GenericRelation('tigacrafting.Taxon')

    def __str__(self):
        return self.description


class OtherSpecies(models.Model):
    name = models.TextField('Name of other species', help_text='List of other, not controlled species')
    category = models.TextField('Subcategory of other species', blank=True, help_text='The subcategory of other species, i.e. Other insects, Culicidae')
    ordering = models.IntegerField('Auxiliary help to tweak list ordering', blank=True, null=True)

    taxa = GenericRelation('tigacrafting.Taxon')

    def __str__(self):
        return self.name


class Taxon(MP_Node):
    @classmethod
    def get_root(cls) -> Optional['Taxon']:
        return cls.get_root_nodes().first()

    @classmethod
    def get_leaves_in_rank_group(cls, rank: int) -> models.QuerySet['Taxon']:
        rank_group = cls._convert_rank_to_rank_group(rank=rank)
        next_rank_group = rank_group + cls.RANK_GROUP_STEP
        return Taxon.objects.filter(
            rank__gte=rank_group,
            rank__lt=next_rank_group
        ).exclude(
            models.Exists(
                Taxon.objects.filter(
                    path__startswith=models.OuterRef('path'),
                    depth__gt=models.OuterRef('depth'),
                    rank__lt=next_rank_group
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
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, null=True, blank=True,
        limit_choices_to={
            'app_label': 'tigacrafting',
            'model__in': (Categories._meta.model_name, Complex._meta.model_name, OtherSpecies._meta.model_name)
        }
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")

    # Attributes - Mandatory
    rank = models.PositiveSmallIntegerField(choices=TaxonomicRank.choices)
    name = models.CharField(max_length=32, unique=True)
    is_relevant = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Indicates if this taxon is relevant for the application. Will be shown first and will set task to conflict if final taxon is not this."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Attributes - Optional
    common_name = models.CharField(max_length=64, null=True, blank=True)

    # Object Manager
    # Custom Properties
    node_order_by = ['name']

    @property
    def is_specie(self):
        return self.rank >= self.TaxonomicRank.SPECIES_COMPLEX

    @cached_property
    def parent(self) -> Optional['Taxon']:
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

    def get_leaves(self) -> models.QuerySet['Taxon']:
        return self.get_descendants().filter(numchild=0)

    def get_parent_in_prev_rank_group(self) -> Optional['Taxon']:
        return self.get_ancestors().filter(rank=self.prev_rank_group).order_by('depth').first()

    def get_children_leaves_in_rank_group(self) -> models.QuerySet['Taxon']:
        return Taxon.get_leaves_in_rank_group(rank=self.next_rank_group).filter(
            path__startswith=self.path
        )

    def get_sibling_leaves_in_rank_group(self) -> models.QuerySet['Taxon']:
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
            10: _("species_culex")
        }

        return translations_table.get(self.pk, _("species_other"))

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
        if self.name:
            self.name = self.name.strip()

        if self.name and self.is_specie:
            # Capitalize only first letter
            self.name = self.name.capitalize()

        self._clean_custom_fields()

        super().save(*args, **kwargs)

    # Meta and String
    class Meta:
        verbose_name = _("taxon")
        verbose_name_plural = _("taxa")
        constraints = [
            models.UniqueConstraint(fields=["name", "rank"], name="unique_name_rank"),
            models.UniqueConstraint(fields=["depth"], condition=models.Q(depth=1), name="unique_root"),
            models.UniqueConstraint(
                fields=["content_type", "object_id"],
                condition=models.Q(content_type__isnull=False, object_id__isnull=False),
                name="unique_content_type_object_id"
            ),
        ]
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} [{self.get_rank_display()}]"


class FavoritedReports(models.Model):
    user = models.ForeignKey(User, related_name='favorited_by', help_text='User which marked the report as favorite', on_delete=models.CASCADE,)
    report = models.ForeignKey('tigaserver_app.Report', related_name='favorites', help_text='User which marked the report as favorite', on_delete=models.CASCADE)
    note = models.TextField('Brief note stating why this report interested you', blank=True, help_text='Add a brief description that will help you remember the report')

    class Meta:
        unique_together = ('user','report',)


class Alert(models.Model):
    xvb = models.BooleanField('Stands for expert validation based - if True, means that the alert was sent after expert validation. For False, it was sent before')
    report_id = models.CharField(help_text='Report related with the alert',max_length=40)
    report_datetime = models.DateTimeField()
    loc_code = models.CharField('Locale code - can be either a nuts3 code, or a nuts3_natcode (natcode is a municipality code) for spanish reports',max_length=25)
    cat_id = models.IntegerField('aima species category id')
    species = models.CharField('Species slug',max_length=25)
    certainty = models.FloatField('IA certainty value')
    status = models.CharField('Introduction status label',max_length=50, default='')
    hit = models.BooleanField('True if AIMA identification was initially correct, False if AIMA initially failed and was revised', blank=True, null=True)
    review_species = models.CharField('Revised species slug, can be empty', max_length=25, blank=True, null=True)
    review_status = models.CharField('Revised introduction status label', max_length=50, blank=True, null=True)
    review_datetime = models.DateTimeField('revision timestamp', blank=True, null=True )
    alert_sent = models.BooleanField('flag for alert sent or not yet', default=False)
    notes = models.TextField('Notes field for varied observations', blank=True, null=True)

# class Species(models.Model):
#     species_name = models.TextField('Scientific name of the objective species or combination of species', blank=True, help_text='This is the species latin name i.e Aedes albopictus')
#     composite = models.BooleanField(default=False, help_text='Indicates if this row is a single species or a combination')


# VALIDATION_CATEGORIES = ((2, 'Sure'), (1, 'Probably'), (0, 'None'))
# class Validation(models.Model):
#     report = models.ForeignKey('tigaserver_app.Report', related_name='report_speciesvalidations')
#     user = models.ForeignKey(User, related_name="user_speciesvalidations")
#     validation_time = models.DateTimeField(blank=True, null=True)
#     species = models.ForeignKey(Species, related_name='validations', blank=True, null=True)
#     #species = models.ManyToManyField(Species)
#     validation_value = models.IntegerField('Validation Certainty', choices=VALIDATION_CATEGORIES, default=None, blank=True, null=True, help_text='Certainty value, 1 for probable, 2 for sure')
