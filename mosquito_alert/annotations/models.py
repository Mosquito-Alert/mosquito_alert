from abc import abstractmethod

from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django_lifecycle import AFTER_UPDATE, LifecycleModelMixin, hook

from mosquito_alert.images.models import Photo
from mosquito_alert.utils.models import TimeStampedModel

####################
# NOTE: Until generic annotations is not needed, only abstractions will be defined.
####################

####################
# Task
####################


class BaseTask(LifecycleModelMixin, TimeStampedModel):
    # Relations
    # Attributes - Mandatory
    # Attributes - Optional
    is_completed = models.BooleanField(default=False)

    # Object Manager

    # Custom Properties
    # Methods
    def _run_on_is_completed_changes(self):
        pass

    @hook(AFTER_UPDATE, when="is_completed", has_changed=True)
    def _run_is_completed_update_hook(self):
        self._run_on_is_completed_changes()

    def _get_is_completed_value(self) -> bool:
        return False

    def update_is_completed(self, *args, **kwargs) -> None:
        self.is_completed = self._get_is_completed_value()

    def save(self, *args, **kwargs):
        if not self._state.adding:
            # It might be using FK, so only can update is_completed after creation.
            if update_fields := kwargs.get("update_fields", None):
                if "is_completed" in update_fields:
                    self.update_is_completed()
            else:
                self.update_is_completed()

        super().save(*args, **kwargs)

    # Meta and String
    class Meta(TimeStampedModel.Meta):
        abstract = True


class BaseAnnotationTask(BaseTask):
    # Relations

    # Attributes - Mandatory
    # Attributes - Optional
    total_annotations = models.PositiveIntegerField(
        default=0,
        db_index=True,
        editable=False,
        help_text="Number of total annotations for the current task except cancelled annotations",
    )

    skipped_annotations = models.PositiveIntegerField(
        default=0,
        db_index=True,
        editable=False,
        help_text="Number of total cancelled annotations for the current task",
    )
    total_predictions = models.PositiveIntegerField(
        default=0, db_index=True, editable=False, help_text="Number of total predictions for the current task"
    )

    # Object Manager
    # Custom Properties

    # Methods
    def _update_counter(self, fieldname: str, inc_value: int):
        with transaction.atomic():
            # See: https://docs.djangoproject.com/en/dev/ref/models/expressions/#avoiding-race-conditions-using-f
            setattr(self, fieldname, models.F(fieldname) + inc_value)
            self.save(update_fields=[fieldname])
            self.refresh_from_db(fields=[fieldname])

    def increase_annotation_counter(self):
        self._update_counter(fieldname="total_annotations", inc_value=1)

    def decrease_annotation_counter(self):
        self._update_counter(fieldname="total_annotations", inc_value=-1)

    def increase_skipped_annotation_counter(self):
        self._update_counter(fieldname="skipped_annotations", inc_value=1)

    def decrease_skipped_annotation_counter(self):
        self._update_counter(fieldname="skipped_annotations", inc_value=-1)

    def increase_prediction_counter(self):
        self._update_counter(fieldname="total_predictions", inc_value=1)

    def decrease_prediction_counter(self):
        self._update_counter(fieldname="total_predictions", inc_value=-1)

    # Meta and String
    class Meta(BaseTask.Meta):
        abstract = True


class BasePhotoAnnotationTask(BaseAnnotationTask):
    # Relations
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE)

    # Attributes - Mandatory
    # Attributes - Optional

    # Object Manager
    # Custom Properties

    # Methods

    # Meta and String
    class Meta:
        abstract = True


####################
# Annotation
####################


class Label(models.Model):
    value = models.JSONField("value", null=False, help_text="Label value")
    title = models.CharField(_("Title"), max_length=2048, help_text="Label title")
    description = models.TextField(_("Description"), help_text="Label description", blank=True, null=True)

    class Meta:
        abstract = True


class BaseAnnotation(models.Model):
    # Relations
    @property
    @abstractmethod
    def label(self):
        raise NotImplementedError
        # label = models.ForeignKey(Label, on_delete=models.PROTECT)

    # Attributes - Mandatory

    # Attributes - Optional

    # Object Manager

    # Custom Properties

    # Meta and String
    class Meta:
        abstract = True

    def __str__(self) -> str:
        return f"{self.label}"


class BasePhotoAnnotation(BaseAnnotation):
    @property
    @abstractmethod
    def task(self):
        raise NotImplementedError

    # task = models.ForeignKey(BasePhotoAnnotationTask, on_delete=models.CASCADE)
    class Meta(BaseAnnotation.Meta):
        abstract = True


####################
# Shape in image
####################


class BaseShape(models.Model):
    class ShapeType(models.TextChoices):
        RECTANGLE = "rectangle", _("rectangle")  # ([x0, y0], [x1, y1])
        # POLYGON = "polygon", _("polygon")  # ([x0, y0], ..., [xn, yn])

    shape_type = models.CharField(max_length=16, choices=ShapeType.choices, default=ShapeType.RECTANGLE)
    # Flattened list of point coordinates
    points = ArrayField(
        ArrayField(
            models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(1)]),  # As percentage of total image
            size=2,
        ),
    )

    # rotation = models.FloatField(default=0)
    @property
    def shape(self):
        from .shapes import get_shape_by_type

        return get_shape_by_type(shape_type=self.shape_type)(points=self.points)

    @shape.setter
    def shape(self, value):
        self.points = value.points
        self.shape_type = value.shape_type

    def clean(self):
        super().clean()

        match self.shape_type:
            case self.ShapeType.RECTANGLE:
                if len(self.points) != 2:
                    raise ValidationError("Points length must be equal to 2. ([x0, y0], [x1, y1])")
            case _:
                pass

    def save(self, *args, **kwargs):
        # Validate points field
        self.full_clean(exclude=[x.name for x in self._meta.fields if x.name not in ["points"]])
        super().save(*args, **kwargs)

    class Meta:
        abstract = True


####################
# Attributes: non-structured information
# Could be understood as metadata for the label
# selected.
# Example:
#    - label: Car
#   -  attribute:
#       - spec: color
#       - value: red
####################


class AttributeSpec(models.Model):
    class AttributeType(models.TextChoices):
        CHECKBOX = "checkbox"
        RADIO = "radio"
        NUMBER = "number"
        TEXT = "text"
        SELECT = "select"

    label = models.ForeignKey(Label, on_delete=models.CASCADE)
    name = models.CharField(max_length=64)
    input_type = models.CharField(max_length=16, choices=AttributeType.choices)
    values = models.CharField(blank=True, max_length=4096)

    class Meta:
        abstract = True
        default_permissions = ()
        unique_together = ("label", "name")

    def __str__(self):
        return self.name


class AttributeVal(models.Model):
    # TODO: add a validator here to be sure that it corresponds to self.label
    spec = models.ForeignKey(AttributeSpec, on_delete=models.CASCADE)
    value = models.CharField(max_length=4096)

    class Meta:
        abstract = True
        default_permissions = ()


####################
# Example of use: image classification
####################


class LabeledPhoto(BasePhotoAnnotation):
    class Meta:
        abstract = True


class LabeledPhotoAttributeVal(AttributeVal):
    photo = models.ForeignKey(LabeledPhoto, on_delete=models.CASCADE)

    class Meta:
        abstract = True


####################
# Example of use: image object detection
####################


class LabeledShape(BasePhotoAnnotation, BaseShape):
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, related_name="elements")

    class Meta:
        abstract = True


class LabeledShapeAttributeVal(AttributeVal):
    shape = models.ForeignKey(LabeledShape, on_delete=models.CASCADE)

    class Meta:
        abstract = True
