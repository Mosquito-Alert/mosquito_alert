from abc import abstractmethod
from decimal import Decimal
from functools import reduce
from itertools import chain
from operator import itemgetter
from statistics import StatisticsError, mode
from typing import List

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from django.dispatch import Signal
from django.utils.translation import gettext_lazy as _
from django_lifecycle import AFTER_CREATE, AFTER_UPDATE, hook

from mosquito_alert.annotations.models import BaseAnnotation, BasePhotoAnnotationTask, BaseShape, BaseTask
from mosquito_alert.annotations.shapes import Rectangle, avg_rectangles, group_rectangles
from mosquito_alert.images.models import Photo
from mosquito_alert.individuals.models import Individual
from mosquito_alert.taxa.models import Taxon
from mosquito_alert.utils.models import ObservableMixin, TimeStampedModel

from .managers import (
    BasePhotoIdentificationManager,
    BaseTaxonAnnotationManager,
    TaxonClassificationCandidateManager,
    UserIdentificationManager,
)
from .prob_tree import TaxonProbNode, create_tree
from .settings import MIN_CONSENSUS_PROB, MIN_IOU, NUM_USER_IDENTIFICATIONS_TO_COMPLETE

####################
# NOTE: Identifications can be understood of
# a specific annotations focused on taxonomy.
####################

####################
# Concepts:
#     - [...]Classification[...]: assign label to the whole concept (answers: what is found)
#     - [...]Identification[...]: assign label to a region of the concept (answers: what is found and where)
####################

####################
# Model schema:
#
# Individual
# └── IndividualIdentificationTask
#     ├── IndividualIdentificationTaskResult(COMMUNITY|ENSEMBLED|COMPUTER VISION|EXTERNAL)
#     │   ├── TaxonClassificationCandidate(is_seed=False)
#     │   ├── TaxonClassificationCandidate(is_seed=False)
#     │   └── [...]
#     ├── PhotoIdentificationTask
#     │   ├── PhotoIdentificationTaskResult
#     │   │   ├── TaxonClassificationCandidate(is_seed=False)
#     │   │   ├── TaxonClassificationCandidate(is_seed=False)
#     │   │   └── [...]
#     │   ├── UserIdentification
#     │   │   ├── TaxonClassificationCandidate(is_seed=True)
#     │   │   ├── TaxonClassificationCandidate(is_seed=False)
#     │   │   └── [...]
#     │   ├── Prediction
#     │   │   ├── TaxonClassificationCandidate(is_seed=True)
#     │   │   ├── TaxonClassificationCandidate(is_seed=False)
#     │   │   └── [...]
#     │   └── ExternalIdentification
#     │       ├── TaxonClassificationCandidate(is_seed=True)
#     │       ├── TaxonClassificationCandidate(is_seed=False)
#     │       └── [...]
#     ├── PhotoIdentificationTask
#     ├── PhotoIdentificationTask
#     └── [...]
####################


# TODO: OrganizationSummary(models.Model) for statistics

classification_has_changed = Signal()
identification_task_has_changed = Signal()

#############################


class BaseTaxonAnnotation(ObservableMixin, BaseAnnotation):
    NOTIFY_ON_FIELD_CHANGE = ["label", "probability"]

    # Relations
    label = models.ForeignKey(
        Taxon, limit_choices_to={"rank__gte": Taxon.TaxonomicRank.CLASS}, on_delete=models.PROTECT
    )  # @override from BaseAnnotation

    # Attributes - Mandatory
    probability = models.DecimalField(
        max_digits=7, decimal_places=6, validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("1"))]
    )

    # Attributes - Optional

    # Object Manager
    objects = BaseTaxonAnnotationManager()

    # Custom Properties
    @property
    def to_tree_node(self) -> TaxonProbNode:
        return TaxonProbNode(taxon=self.taxon, probability=self.probability)

    @property
    def taxon(self) -> Taxon:
        return self.label

    @taxon.setter
    def taxon(self, value):
        self.label = value

    # Methods
    def _notify_changes(self, fields_changed=[]):
        if fields_changed := list(filter(lambda x: x in self.NOTIFY_ON_FIELD_CHANGE, fields_changed)):
            classification_has_changed.send(sender=self.__class__, instance=self, fields_changed=fields_changed)

    # Meta and String
    class Meta(BaseAnnotation.Meta):
        abstract = True
        constraints = [
            models.CheckConstraint(
                check=models.Q(probability__range=(Decimal("0"), Decimal("1"))),
                name="%(app_label)s_%(class)s_probability_min_max_value",
            )
        ]

    def __str__(self) -> str:
        return f"{self.taxon} (p={self.probability})"


def validator_content_type_issubclass(content_type_id):
    content_type = ContentType.objects.get_for_id(id=content_type_id)
    if not issubclass(content_type.model_class(), BaseClassification):
        raise ValidationError("content_object must be subclass of BaseClassification")


class TaxonClassificationCandidate(BaseTaxonAnnotation, TimeStampedModel):
    NOTIFY_ON_FIELD_CHANGE = BaseTaxonAnnotation.NOTIFY_ON_FIELD_CHANGE + ["is_seed"]

    # Relations
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, validators=[validator_content_type_issubclass]
    )
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    # Attributes - Mandatory
    # Attributes - Optional
    is_seed = models.BooleanField(default=False)

    # Object Manager
    objects = TaxonClassificationCandidateManager()

    # Custom Properties
    @property
    def to_tree_node(self) -> TaxonProbNode:
        obj = super().to_tree_node
        obj.is_seed = self.is_seed
        return obj

    # Methods
    def clean(self) -> None:
        super().clean()

        if self.pk and self.is_seed:
            if not issubclass(self.content_type.model_class(), BasePhotoIdentification):
                raise ValidationError("is_seed can only be true for objects subclasses of BasePhotoIdentification")

    def save(self, *args, **kwargs):
        self.full_clean(exclude=[x.name for x in self._meta.fields if x.name not in ["content_type"]])

        super().save(*args, **kwargs)

    # Meta and String
    class Meta(BaseTaxonAnnotation.Meta, TimeStampedModel.Meta):
        constraints = (
            BaseTaxonAnnotation.Meta.constraints
            + TimeStampedModel.Meta.constraints
            + [
                models.UniqueConstraint(
                    fields=["content_type", "object_id", "label"],
                    name="unique_classification_candidate_by_label",
                )
            ]
        )
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]


class BaseClassification(ObservableMixin, models.Model):
    NOTIFY_ON_FIELD_CHANGE = ["sex", "candidates"]

    class SexOptions(models.TextChoices):
        FEMALE = "F", _("Female")
        MALE = "M", _("Male")

    # Relations
    candidates = GenericRelation(TaxonClassificationCandidate, related_query_name="result")

    # Attributes - Mandatory
    # Attributes - Optional
    # NOTE: In case more and more attributes need to be annotates, please
    #       consider using annotations.models.AttributeSpec; and implement
    #       a voting/polling system.
    sex = models.CharField(max_length=1, choices=SexOptions.choices, blank=True, null=True)

    # Object Manager
    # Custom Properties

    # Methods
    def _notify_changes(self, fields_changed=[]):
        if fields_changed := list(filter(lambda x: x in self.NOTIFY_ON_FIELD_CHANGE, fields_changed)):
            classification_has_changed.send(sender=self.__class__, instance=self, fields_changed=fields_changed)

    def get_classification_tree(self) -> TaxonProbNode:
        if candidates := self.candidates.all():
            nodes = [x.to_tree_node for x in candidates.all()]

            root_node = min(nodes, key=lambda x: x.taxon.rank)
            nodes.remove(root_node)

            root_node.link_descendants(nodes=nodes)
        else:
            # Return root taxon if candidates not found.
            root_node = TaxonProbNode(taxon=Taxon.get_root(), probability=1)

        return root_node

    def recompute_candidates_tree(self) -> bool:
        # Only consider the seed nodes.
        qs_seed_candidates = self.candidates.filter(is_seed=True)
        seeds_found = False
        if qs_seed_candidates.exists():
            # If at least one seed
            candidates = qs_seed_candidates.all()
            seeds_found = True
        else:
            candidates = self.candidates.all()

        if candidates:
            nodes = [x.to_tree_node for x in candidates]
        else:
            nodes = [TaxonProbNode(taxon=Taxon.get_root(), probability=1)]

        new_tree = create_tree(nodes=nodes)

        if not seeds_found:
            new_tree._apply_func_to_children(func=lambda x: setattr(x, "is_seed", False), include_self=True)

        return self.update_candidates_from_tree(tree=new_tree)

    def update_candidates_from_tree(self, tree: TaxonProbNode) -> bool:
        tree_nodes = [tree.root] + list(tree.root.descendants) if tree else []

        with transaction.atomic():
            # Delete objects that does not exist in the tree but exist in the DB.
            num_deleted, _ = self.candidates.exclude(label__pk__in=[x.taxon.pk for x in tree_nodes]).delete()
            has_deleted = bool(num_deleted)

            has_created = False
            has_updated = False
            for node in tree_nodes:
                try:
                    # Try to fetch from the DB
                    obj = TaxonClassificationCandidate.objects.get(
                        content_type=ContentType.objects.get_for_model(self),
                        object_id=self.pk,
                        label=node.taxon,
                    )
                except TaxonClassificationCandidate.DoesNotExist:
                    # Create new
                    obj = TaxonClassificationCandidate(
                        content_object=self,
                        label=node.taxon,
                        probability=node.probability,
                        is_seed=node.is_seed,
                        skip_notify_changes=True,  # skip notify self on create
                    )
                    obj.save()
                    has_created = True
                else:
                    # Update probability/is_seed if is different
                    if any([obj.probability != node.probability, obj.is_seed != node.is_seed]):
                        # Skip notify changes again to self
                        obj.skip_notify_changes = True
                        # Set new attributes
                        obj.probability = node.probability
                        obj.is_seed = node.is_seed
                        # Save
                        obj.save()
                        has_updated = True

                obj.skip_notify_changes = False

            has_changes = has_deleted or has_created or has_updated

        if has_changes:
            self.save(update_fields=["updated_at"])

            if not self.skip_notify_changes:
                self._notify_changes(fields_changed=["candidates"])

        return has_changes

    # Meta and String
    class Meta:
        abstract = True


class BaseIdentification(BaseClassification, BaseShape):  # Object identification
    NOTIFY_ON_FIELD_CHANGE = BaseClassification.NOTIFY_ON_FIELD_CHANGE + ["points", "shape_type"]

    # Relations
    # Attributes - Mandatory
    # Attributes - Optional
    # Object Manager

    # Custom Properties
    # Methods
    # Meta and string
    class Meta(BaseShape.Meta, BaseClassification.Meta):
        abstract = True


##########################
# Task definition
##########################


class BaseTaskWithResults(BaseTask):
    _results_related_name = "results"

    @abstractmethod
    def _run_on_result_change(self) -> None:
        raise NotImplementedError

    def update_results(self) -> bool:
        result_cls = getattr(self, self._results_related_name).model

        has_created, has_changed = False, False
        for result_type in result_cls.ResultType:
            try:
                # Try to fetch from the DB
                obj = result_cls.objects.get(task=self, type=result_type)
            except result_cls.DoesNotExist:
                # Create new
                obj = result_cls(task=self, type=result_type, skip_notify_changes_parent=True)
                obj.save()
                has_created = True
            finally:
                obj.skip_notify_changes_parent = True
                obj_has_changed = obj.recompute_result(from_candidates=False)
                if obj_has_changed:
                    has_changed = True

        obj.skip_notify_changes_parent = False

        has_updated = has_changed or has_created

        if has_updated:
            self._run_on_result_change()

        return has_updated

    def _run_on_is_completed_changes(self):
        identification_task_has_changed.send(sender=self.__class__, instance=self, fields_changed=["is_completed"])

    class Meta(BaseTask.Meta):
        abstract = True


class BaseTaskChildMeta(models.base.ModelBase):
    def __new__(cls, name, bases, attrs, task_model=None, related_name=None, **kwargs):
        if task_model:
            if not issubclass(task_model, BaseTaskWithResults):
                raise ValueError(f"task_model must be subclass of {BaseTaskWithResults}")
            attrs["task"] = models.ForeignKey(
                task_model, on_delete=models.CASCADE, editable=False, related_name=related_name
            )
        return super().__new__(cls, name, bases, attrs, **kwargs)


class BaseTaskChild(ObservableMixin, TimeStampedModel, metaclass=BaseTaskChildMeta):
    # Relations
    # NOTE: task FK defined in metaclass

    # Attributes - Mandatory
    # Attributes - Optional
    # Object Manager

    # Custom Properties

    # Methods
    def __init__(self, *args, **kwargs):
        # NOTE: __init__ signature can not be changed
        # See: https://docs.djangoproject.com/en/dev/ref/models/instances/#django.db.models.Model
        self.skip_notify_changes_parent = kwargs.pop("skip_notify_changes_parent", False)
        super().__init__(*args, **kwargs)

    def _run_on_notify_changes_to_parent(self):
        self.task.save(update_fields=["updated_at", "is_completed"])

    def notify_changes_to_parent(self):
        if not self.skip_notify_changes_parent:
            self._run_on_notify_changes_to_parent()

    def _notify_changes(self, fields_changed=[]):
        super()._notify_changes(fields_changed)
        self.notify_changes_to_parent()

    # Meta and String
    class Meta(TimeStampedModel.Meta):
        abstract = True


class IndividualIdentificationTask(BaseTaskWithResults):
    # Relations
    photos = models.ManyToManyField(Photo, through="PhotoIdentificationTask")
    individual = models.OneToOneField(
        Individual, on_delete=models.CASCADE, primary_key=True, editable=False, related_name="identification_task"
    )

    # Attributes - Mandatory
    # Attributes - Optional
    # TODO: locked_by (user/organization)/ lock_expire_at. Use settings.TASK_LOCK_DEFAULT_TTL
    is_locked = models.BooleanField(default=False, help_text=_("Whether it accepts or not more annotations."))

    # Object Manager

    # Custom Properties

    # Methods
    def _run_on_result_change(self):
        pass

    def _get_is_completed_value(self) -> bool:
        return self.photo_identification_tasks.filter(is_completed=True).exists()

    # Meta and String
    class Meta(BaseTaskWithResults.Meta):
        verbose_name = _("individual identification task")
        verbose_name_plural = _("individual identification tasks")
        permissions = [("can_lock_tasks", _("Can lock identification tasks"))]


class PhotoIdentificationTask(BaseTaskWithResults, BaseTaskChild, BasePhotoAnnotationTask):
    """Task of identifying a single individual in an image."""

    NOTIFY_ON_FIELD_CHANGE = ["is_completed"]

    # Relations
    task = models.ForeignKey(
        IndividualIdentificationTask,
        on_delete=models.CASCADE,
        editable=False,
        related_name="photo_identification_tasks",
    )

    # Attributes - Mandatory
    # Attributes - Optional
    total_external = models.PositiveIntegerField(
        default=0,
        db_index=True,
        editable=False,
        help_text="Number of total external identifications for the current task.",
    )

    # Object Manager
    # Custom Properties
    @property
    def individual(self):
        return self.task.individual

    @property
    def is_locked(self):
        return self.task.is_locked

    # Methods
    def _get_is_completed_value(self) -> bool:
        if self.is_completed and self.total_annotations:
            # keep state.
            return True

        return (self.total_annotations >= NUM_USER_IDENTIFICATIONS_TO_COMPLETE) or getattr(
            self, self._results_related_name
        ).filter(is_ground_truth=True).exists()

    def _run_on_result_change(self):
        self.task.update_results()

    def increase_external_counter(self):
        self._update_counter(fieldname="total_external", inc_value=1)

    def decrease_external_counter(self):
        self._update_counter(fieldname="total_external", inc_value=-1)

    # Meta and String
    class Meta(BaseTaskWithResults.Meta, BasePhotoAnnotationTask.Meta):
        verbose_name = _("photo identification task")
        verbose_name_plural = _("photo identification tasks")
        default_related_name = "photo_identification_tasks"
        constraints = BaseTaskWithResults.Meta.constraints + [
            models.UniqueConstraint(
                fields=["task", "photo"],
                name="unique_task_photo",
            )
        ]


##########################
# Identification definition
##########################


class BasePhotoIdentification(BaseTaskChild, BaseIdentification, task_model=PhotoIdentificationTask):
    # Relations
    # NOTE: task FK is set on metaclass
    NOTIFY_ON_FIELD_CHANGE = BaseTaskChild.NOTIFY_ON_FIELD_CHANGE + BaseIdentification.NOTIFY_ON_FIELD_CHANGE

    # Attributes - Mandatory
    # Attributes - Optional
    # Object Manager
    objects = BasePhotoIdentificationManager()

    # Custom Properties
    # Methods
    def _run_on_notify_changes_to_parent(self):
        super()._run_on_notify_changes_to_parent()
        self.task.update_results()

    def save(self, *args, **kwargs):
        if self.task.is_locked:
            raise ValueError("Can not create/edit photo identifications when the task is locked.")

        return super().save(*args, **kwargs)

    # Meta and String
    class Meta(BaseTaskChild.Meta, BaseIdentification.Meta):
        abstract = True


class UserIdentification(BasePhotoIdentification):
    NOTIFY_ON_FIELD_CHANGE = BasePhotoIdentification.NOTIFY_ON_FIELD_CHANGE + ["is_ground_truth", "was_skipped"]

    # Relations
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="identifications",
        limit_choices_to={"profile__is_identifier": True},
    )

    # Attributes - Mandatory

    # Attributes - Optional
    lead_time = models.FloatField(
        _("lead time"), null=True, default=None, editable=False, help_text="How much time it took to annotate the task"
    )
    # TODO: allow only is_superidentifier to toggle this.
    is_ground_truth = models.BooleanField(default=False)

    was_skipped = models.BooleanField(default=False, help_text="User skipped the task")

    # Object Manager
    objects = UserIdentificationManager()

    # Custom Properties
    # Methods
    @hook(AFTER_CREATE)
    def _update_task_counters_on_create(self):
        if self.was_skipped:
            self.task.increase_skipped_annotation_counter()
        else:
            self.task.increase_annotation_counter()

    @hook(AFTER_UPDATE, when="was_skipped", has_changed=True)
    def _update_task_skipped_counter(self):
        with transaction.atomic():
            if self.was_skipped:
                self.task.decrease_annotation_counter()
                self.task.increase_skipped_annotation_counter()
            else:
                self.task.decrease_skipped_annotation_counter()
                self.task.increase_annotation_counter()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        if self.was_skipped:
            self.task.decrease_skipped_annotation_counter()
        else:
            self.task.decrease_annotation_counter()

    # Meta and String
    class Meta(BasePhotoIdentification.Meta):
        verbose_name = _("user identification")
        verbose_name_plural = _("user identifications")
        default_related_name = "user_identifications"
        constraints = BasePhotoIdentification.Meta.constraints + [
            models.UniqueConstraint(  # Allow single user identification for each task.
                fields=["user", "task"],
                name="unique_user_task",
            ),
            models.UniqueConstraint(  # Allow single ground truth for each task.
                fields=["task"],
                condition=models.Q(is_ground_truth=True),
                name="unique_user_identification_ground_truth_task",
            ),
            models.CheckConstraint(
                check=models.Q(is_ground_truth=False) | models.Q(is_ground_truth=True) & models.Q(was_skipped=False),
                name="skipped_identification_can_not_be_ground_truth",
            ),
        ]


class Prediction(BasePhotoIdentification):
    # Relations
    # TODO: ml_model = models.ForeignKey(MLModel) + constraints

    # Attributes - Mandatory

    # Attributes - Optional
    # Object Manager

    # Custom Properties

    # Methods
    @hook(AFTER_CREATE)
    def _increase_task_prediction_counter(self):
        self.task.increase_prediction_counter()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.task.decrease_prediction_counter()

    # Meta and String
    class Meta(BasePhotoIdentification.Meta):
        verbose_name = _("taxon image prediction run")
        verbose_name_plural = _("taxon image predictions runs")
        default_related_name = "predictions"


class ExternalIdentification(BasePhotoIdentification):
    # Relations

    # Attributes - Mandatory

    # Attributes - Optional

    # Object Manager

    # Custom Properties

    # Methods
    @hook(AFTER_CREATE)
    def _increase_task_external_counter(self):
        self.task.increase_external_counter()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.task.decrease_external_counter()

    # Meta and String
    class Meta(BasePhotoIdentification.Meta):
        verbose_name = _("external identification")
        verbose_name_plural = _("external identifications")
        default_related_name = "external_identifications"


##########################
# Task Results
##########################


class BaseTaskResultMeta(BaseTaskChildMeta):
    def __new__(cls, name, bases, attrs, task_model=None, **kwargs):
        return super().__new__(
            cls,
            name,
            bases,
            attrs,
            task_model=task_model,
            related_name=BaseTaskWithResults._results_related_name,
            **kwargs,
        )


class BaseTaskResult(BaseTaskChild, metaclass=BaseTaskResultMeta):
    class ResultType(models.TextChoices):
        COMMUNITY = "com", _("Community")  # User based only
        COMPUTER_VISION = "cv", _("Computer Vision")  # CV based only
        ENSEMBLED = "ens", _("Ensembled")  # User + CV based
        EXTERNAL = "ext", _("External")  # From other sources than MosquitoAlert

    # Relations
    # NOTE: task FK is created in the metaclass
    type = models.CharField(max_length=3, choices=ResultType.choices)

    # Attributes - Mandatory
    # Attributes - Optional
    # Object Manager
    # Custom Properties
    # Methods
    @abstractmethod
    def recompute_result() -> bool:
        raise NotImplementedError

    def _run_on_notify_changes_to_parent(self):
        super()._run_on_notify_changes_to_parent()
        self.task._run_on_result_change()

    # Meta and String
    class Meta(BaseTaskChild.Meta):
        abstract = True
        constraints = BaseTaskChild.Meta.constraints + [
            models.UniqueConstraint(fields=["task", "type"], name="%(app_label)s_%(class)s_unique_task_type")
        ]


class BaseClassificationTaskResult(BaseTaskResult, BaseClassification, BaseTaxonAnnotation):
    NOTIFY_ON_FIELD_CHANGE = list(
        set(BaseTaxonAnnotation.NOTIFY_ON_FIELD_CHANGE + BaseClassification.NOTIFY_ON_FIELD_CHANGE)
    )

    # NOTE: All fields that are vote controlled (most common). Must be defined in BaseClassification
    FIELDS_PUT_TO_THE_VOTE = ("sex",)

    # Attributes - Mandatory
    # Attributes - Optional
    # Object Manager

    # Custom Properties
    @property
    @abstractmethod
    def related_classifications(self) -> list[BaseClassification]:
        raise NotImplementedError

    # Methods
    def _recompute_attributes(
        self,
        fields: list[str] = FIELDS_PUT_TO_THE_VOTE,
        commit: bool = True,
    ) -> bool:
        has_changed = False

        for f in fields:
            try:
                most_common_value = mode(data=[getattr(x, f) for x in self.related_classifications])
            except StatisticsError:
                # Case empty related_classifications
                most_common_value = None

            if getattr(self, f) != most_common_value:
                setattr(self, f, most_common_value)
                has_changed = True

        if has_changed and commit:
            self.save()

        return has_changed

    @abstractmethod
    def _recompute_candidates(self) -> bool:
        raise NotImplementedError

    def _recompute_label_consensus(self, commit=True, min_prob=MIN_CONSENSUS_PROB, min_taxon_rank=None) -> bool:
        has_changed = False

        try:
            taxon_consensus = self.candidates.all().get_consensus(min_prob=min_prob, min_taxon_rank=min_taxon_rank)
        except TaxonClassificationCandidate.DoesNotExist:
            new_taxon = Taxon.get_root()
            new_probability = Decimal("1")
        else:
            new_taxon = taxon_consensus.taxon
            new_probability = taxon_consensus.probability

        has_changed = any([getattr(self, "label", None) != new_taxon, self.probability != new_probability])

        self.label = new_taxon
        self.probability = new_probability

        if commit and has_changed:
            self.save()

        return has_changed

    def recompute_result(self, commit=True, from_candidates=True, *args, **kwargs) -> bool:
        with transaction.atomic():
            if not from_candidates:
                self._recompute_candidates()

            has_changed_attrs = self._recompute_attributes(commit=False)

            has_changed_label = self._recompute_label_consensus(commit=False, *args, **kwargs)

            has_changed = has_changed_attrs or has_changed_label

            if commit and has_changed:
                self.save()

        return has_changed

    def save(self, *args, **kwargs):
        if not hasattr(self, "label"):
            self.label = Taxon.get_root()
            self.probability = 1

        super().save(*args, **kwargs)

    # Meta and String
    class Meta(BaseTaskResult.Meta, BaseClassification.Meta, BaseTaxonAnnotation.Meta):
        abstract = True
        constraints = BaseTaxonAnnotation.Meta.constraints + BaseTaskResult.Meta.constraints


class BaseIdentificationTaskResult(BaseClassificationTaskResult, BaseShape):
    NOTIFY_ON_FIELD_CHANGE = BaseClassificationTaskResult.NOTIFY_ON_FIELD_CHANGE + ["points", "shape_type"]

    # Relations
    # Attributes - Mandatory

    # Attributes - Optional

    # Object Manager
    # Custom Properties
    @property
    @abstractmethod
    def relevant_photo_identifications(self) -> list[BasePhotoIdentification]:
        raise NotImplementedError

    # Methods
    @abstractmethod
    def _recompute_shape(self, commit=True) -> bool:
        raise NotImplementedError

    def save(self, *args, **kwargs):
        if not self.points:
            self.shape_type = BaseShape.ShapeType.RECTANGLE
            self.points = [[0, 0], [1, 1]]

        super().save(*args, **kwargs)

    # Meta and String
    class Meta(BaseClassificationTaskResult.Meta, BaseShape.Meta):
        abstract = True


class IndividualIdentificationTaskResult(BaseClassificationTaskResult, task_model=IndividualIdentificationTask):
    # Relations

    # Attributes - Mandatory

    # Attributes - Optional

    # Object Manager
    # Custom Properties
    @property
    def related_classifications(self) -> "List[PhotoIdentificationTaskResult]":
        if not self.photo_identification_results.exists():
            return []

        try:
            ground_truth = self.photo_identification_results.filter(is_ground_truth=True).latest("updated_at")
        except PhotoIdentificationTaskResult.DoesNotExist:
            result = list(self.photo_identification_results.all())
        else:
            result = [ground_truth]

        return result

    @property
    def photo_identification_results(self) -> "models.QuerySet[PhotoIdentificationTaskResult]":
        return PhotoIdentificationTaskResult.objects.filter(task__task=self.task, type=self.type)

    # Methods
    def _recompute_candidates(self) -> bool:
        new_tree = None
        # Weight each photo task result by the number of identifications that have contributed.
        if related_classifications := self.related_classifications:
            total_identifications = sum([x.num_contributions for x in related_classifications])
            if total_identifications != 0:
                new_tree = sum(
                    map(
                        lambda x: x.get_classification_tree() * (x.num_contributions / total_identifications),
                        related_classifications,
                    )
                )

        # self.skip_notify_changes = True
        has_changed = self.update_candidates_from_tree(tree=new_tree)
        # self.skip_notify_changes = False

        return has_changed

    # Meta and String
    class Meta(BaseClassificationTaskResult.Meta):
        verbose_name = _("individual identification task result")
        verbose_name_plural = _("individual identification task results")


class PhotoIdentificationTaskResult(BaseIdentificationTaskResult, task_model=PhotoIdentificationTask):
    AGG_WEIGHTS_BY_TYPE = {
        # NOTE: weights must be list (to equally distributed weight), or dict which value sum up 1.
        BaseTaskResult.ResultType.COMMUNITY: (UserIdentification,),
        BaseTaskResult.ResultType.COMPUTER_VISION: (Prediction,),
        BaseTaskResult.ResultType.ENSEMBLED: {
            UserIdentification: 0.65,
            Prediction: 0.25,
            ExternalIdentification: 0.1,
        },
        BaseTaskResult.ResultType.EXTERNAL: (ExternalIdentification,),
    }

    @staticmethod
    def _average_photo_identifications_by_model(
        photo_identifications: list[BasePhotoIdentification],
    ) -> dict[type, TaxonProbNode]:
        # Grouping models by its type
        grouped_identifications_by_model = {}
        for item in photo_identifications:
            grouped_identifications_by_model.setdefault(type(item), []).append(item)

        grouped_trees = {}
        # Intra model averaging
        for klass, g in grouped_identifications_by_model.items():
            # Average
            def avg_tree_func(tree: TaxonProbNode) -> TaxonProbNode:
                return tree * (1 / len(g))

            map_tree_func = avg_tree_func
            if klass == UserIdentification:
                # NOTE: this could be adapted to use each user's identification precision/weight
                def weighted_avg_tree_func(tree: TaxonProbNode) -> TaxonProbNode:
                    return tree * (1 / len(g))

                map_tree_func = weighted_avg_tree_func
            elif klass == Prediction:
                # TODO: get first by model version.
                # In case multiple predictions, get last by updated_at.
                if len(g) > 1:
                    # Will be sorted ascending. Most recent element at the end.
                    # Cast to list for consistency.
                    g = [sorted(g, key=lambda x: x.updated_at)[-1]]

            g_trees = map(map_tree_func, map(lambda x: x.get_classification_tree(), g))
            result_tree = reduce(lambda x, y: x + y, g_trees)
            result_tree._apply_func_to_children(func=lambda x: setattr(x, "is_seed", False), include_self=True)

            grouped_trees[klass] = result_tree

        return grouped_trees

    @classmethod
    def get_identification_classes_by_type(cls, type) -> tuple[type]:
        result = cls.AGG_WEIGHTS_BY_TYPE[type]
        if isinstance(result, dict):
            result = result.keys()

        if not isinstance(result, tuple):
            result = tuple(result)

        return result

    @classmethod
    def get_identification_classes_weights_by_type(cls, type) -> dict[type, float]:
        result = cls.AGG_WEIGHTS_BY_TYPE[type]

        if not isinstance(result, dict):
            if not isinstance(result, list):
                result = list(result)
            # Distributing weight across all elements
            result = {x: 1 / len(result) for x in result}

        return result

    @classmethod
    def get_normalized_weights_by_type(cls, type: str, classes_in_use: list[type]) -> dict[type, float]:
        original_weights = cls.get_identification_classes_weights_by_type(type=type)

        total_weight_in_use = sum([original_weights.get(x, 0) for x in classes_in_use])
        if total_weight_in_use == 0:
            return {}

        return {klass: original_weights.get(klass) / total_weight_in_use for klass in classes_in_use}

    # Relations
    user_identifications = models.ManyToManyField(
        UserIdentification, editable=False, help_text=_("User identifications that contribute to this result.")
    )
    predictions = models.ManyToManyField(
        Prediction, editable=False, help_text=_("Predictions that contribute to this result.")
    )
    external_identifications = models.ManyToManyField(
        ExternalIdentification, editable=False, help_text=_("External identifications that contribute to this result.")
    )

    # Attributes - Mandatory

    # Attributes - Optional
    is_ground_truth = models.BooleanField(default=False, editable=False)

    # Object Manager
    # Custom properties
    @property
    def relevant_photo_identifications(self) -> list[BasePhotoIdentification]:
        return self._get_relevant_photo_identifications(
            identifications=list(
                chain(
                    *[list(klass.objects.filter(task=self.task).finished()) for klass in self.identification_classes]
                )
            )
        )

    @property
    def identification_classes(self) -> tuple[BasePhotoIdentification]:
        return self.get_identification_classes_by_type(type=self.type)

    @property
    def inter_identification_aggr_weights(self) -> dict[BasePhotoIdentification, float]:
        return self.get_identification_classes_weights_by_type(type=self.type)

    @property
    def num_contributions(self):
        return len(self.related_classifications)

    @property
    def related_classifications(self) -> list[BasePhotoIdentification]:
        return (
            list(self.user_identifications.all())
            + list(self.predictions.all())
            + list(self.external_identifications.all())
        )

    # Methods
    def _get_relevant_photo_identifications(
        self, identifications: list[BasePhotoIdentification]
    ) -> list[BasePhotoIdentification]:
        # Filter out all those identifications which class is not going to be used.
        identifications = list(filter(lambda x: isinstance(x, self.identification_classes), identifications))

        # If the community opinion is needed, check if there is any identification marked
        # as is_ground_truth, if so, only use that.
        # Otherwise, use all the user identifications.
        if UserIdentification in self.identification_classes:
            ground_truth_list = sorted(
                filter(lambda x: getattr(x, "is_ground_truth", False), identifications), key=lambda x: x.updated_at
            )

            if ground_truth_list:
                identifications = [ground_truth_list[-1]]

        return identifications

    def _get_resulting_identification_tree(self):
        # 1. Intra model averaging
        grouped_trees = self._average_photo_identifications_by_model(
            photo_identifications=self.related_classifications
        )

        # 2. Inter model averaging.
        # Get normalized weights
        normalized_weights = self.get_normalized_weights_by_type(type=self.type, classes_in_use=grouped_trees.keys())

        if not normalized_weights:
            return TaxonProbNode(taxon=Taxon.get_root(), probability=1)

        return sum([tree * normalized_weights[klass] for klass, tree in grouped_trees.items()])

    def _recompute_candidates(self) -> bool:
        has_changed_shape = self._recompute_shape(commit=True)

        has_ground_truth_changed = self.update_is_ground_truth(commit=True)

        # self.skip_notify_changes = True
        has_changed = self.update_candidates_from_tree(tree=self._get_resulting_identification_tree())
        # self.skip_notify_changes = False
        return has_changed or has_changed_shape or has_ground_truth_changed

    def _recompute_shape(self, commit=True) -> bool:
        identifications = self.relevant_photo_identifications

        # Group shapes
        shape_to_ident_dict = {x.shape: x for x in identifications}

        if not shape_to_ident_dict:
            shape_to_ident_dict = {Rectangle(points=[[0, 0], [1, 1]]): None}

        groups = group_rectangles(rectangles=shape_to_ident_dict.keys(), min_iou=MIN_IOU)

        # Sort by:
        #     1. length of the group
        #     2. Number of shapes comming from UserIdentications.
        # e.g: we need to be sure that if a user contradicts a CV system, the user opnion wins.
        best_group = sorted(
            groups,
            key=lambda group: (
                len(group),  # Size of the group
                sum(
                    isinstance(shape_to_ident_dict.get(s), UserIdentification) for s in group
                ),  # Counter of UserIdentications in the group
            ),
            reverse=True,
        )[0]

        # Replace the new shape
        new_shape = avg_rectangles(rectangles=best_group)

        # Save only the identifications that has contributed
        identification_contributed = itemgetter(*best_group)(shape_to_ident_dict)
        if not isinstance(identification_contributed, (list, tuple)):
            identification_contributed = [identification_contributed]

        for f in ["user_identifications", "predictions", "external_identifications"]:
            contributions = list(
                filter(lambda x: isinstance(x, self._meta.get_field(f).related_model), identification_contributed)
            )
            if contributions:
                getattr(self, f).set(objs=contributions)
            else:
                getattr(self, f).clear()

        # Update shape value
        has_changed = new_shape != self.shape
        if has_changed:
            self.shape = new_shape

        if commit and has_changed:
            self.save()

        return has_changed

    def update_is_ground_truth(self, commit=False, *args, **kwargs) -> bool:
        old_value = self.is_ground_truth
        if self.type == self.ResultType.COMMUNITY:
            self.is_ground_truth = any(
                map(lambda x: getattr(x, "is_ground_truth", False), self.related_classifications)
            )

        has_changed = old_value != self.is_ground_truth
        if commit and has_changed:
            self.save()

        return has_changed

    # Meta and String
    class Meta(BaseIdentificationTaskResult.Meta):
        verbose_name = _("photo identification task result")
        verbose_name_plural = _("photo identification task results")
        constraints = BaseIdentificationTaskResult.Meta.constraints + [
            models.UniqueConstraint(  # Allow single ground truth for each task.
                fields=["task"],
                condition=models.Q(is_ground_truth=True),
                name="unique_photo_ground_truth_task",
            ),
            models.CheckConstraint(
                check=(
                    models.Q(is_ground_truth=False)
                    | (models.Q(is_ground_truth=True, type=BaseTaskResult.ResultType.COMMUNITY))
                ),
                name="only_community_result_allows_ground_truth",
            ),
        ]
