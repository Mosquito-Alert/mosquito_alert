from django.conf import settings
from django.db import models
from django.db.models.signals import ModelSignal
from django.utils.translation import gettext_lazy as _
from django_lifecycle import AFTER_UPDATE, BEFORE_UPDATE, LifecycleModel, hook

from mosquito_alert.images.models import Photo
from mosquito_alert.notifications.signals import notify, notify_subscribers
from mosquito_alert.taxa.models import Taxon

post_identification_changed = ModelSignal(use_caching=True)


class Individual(LifecycleModel):

    # Relations
    taxon = models.ForeignKey(
        Taxon,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="individuals",
    )

    # Attributes - Mandatory
    is_identified = models.BooleanField(default=False, editable=False)
    photos = models.ManyToManyField(Photo, blank=True, related_name="individuals")

    # Attributes - Optional
    # Object Manager

    # Custom Properties

    # Methods
    @hook(BEFORE_UPDATE, when="taxon", has_changed=True)
    def update_is_identified_on_taxon_change(self):
        self.is_identified = self.taxon.is_specie if self.taxon else False

    @hook(AFTER_UPDATE, when="taxon", has_changed=True, is_not=None)
    def notify_identification(self):
        # TODO: use signals and notify in reports app.
        if not self.is_identified:
            return

        post_identification_changed.send(sender=self.__class__, instance=self)

        if hasattr(self, "reports"):
            for r in self.reports.all():
                if user := r.user:
                    notify.send(
                        recipient=user,
                        sender=r,
                        verb="was identified as",
                        action_object=self.taxon,
                        description="Your observation report has been identified as {}".format(
                            self.taxon
                        ),
                    )
                for b in r.location.boundaries.all():
                    notify_subscribers.send(
                        sender=self.taxon,
                        verb="was identified in",
                        target=b,
                    )
        else:
            notify_subscribers.send(
                sender=self.taxon,
                verb="was identified",
            )

    def delete(self, *args, **kwargs):
        # TODO delete orphan images with no reports assigne to them.
        super().delete(*args, **kwargs)

    # Meta and String
    class Meta:
        verbose_name = _("individual")
        verbose_name_plural = _("individuals")

    def __str__(self) -> str:
        return (
            str(self.taxon)
            if self.taxon
            else f"Not-identified individual (id={self.pk})"
        )


class AnnotationAttribute(models.Model):
    # Relations
    # Those taxon that can be questioned with this anntoations: life, mammals, culex pipiens, etc
    taxa = models.ForeignKey(
        Taxon, on_delete=models.CASCADE, related_name="annotation_attributes"
    )

    # Attributes - Mandatory
    label = models.CharField(max_length=128)  # the question
    # datatype = # TODO: numerics, text, choices

    # Attributes - Optional
    # Object Manager

    # Custom Properties

    # Methods

    # Meta and String
    class Meta:
        verbose_name = _("annotation attribute")
        verbose_name_plural = _("annotation attributes")

    def __str__(self) -> str:
        return self.label


class AnnotationValue(models.Model):

    # Relations
    annotation_attribute = models.ForeignKey(
        AnnotationAttribute, on_delete=models.CASCADE, related_name="values"
    )
    taxa = models.ForeignKey(
        Taxon, on_delete=models.CASCADE, related_name="annotation_values"
    )  # Those taxon that can be questioned with this anntoations: life, mammals, culex pipiens, etc

    # Attributes - Mandatory
    label = models.CharField(
        max_length=128
    )  # Dead, Alive | egg, pupa (only a set of taxons)

    # Attributes - Optional
    # Object Manager

    # Custom Properties

    # Methods
    def save(self, *args, **kwargs) -> None:

        if (
            self.taxa != self.annotation_attribute.taxa
            or not self.taxa.is_descendant_of(self.annotation_attribute.taxa)
        ):
            raise ValueError(
                "Tried to assign an annotation value to a taxa that is not "
                "same/descendant of annotation's attribute taxa."
            )

        super().save(*args, **kwargs)

    # Meta and String
    class Meta:
        verbose_name = _("annotation value")
        verbose_name_plural = _("annotation values")

    def __str__(self) -> str:
        return f"{self.label} ({self.annotation_attribute.label})"


class Annotation(models.Model):

    # Relations
    annotation_attribute = models.ForeignKey(
        AnnotationAttribute, on_delete=models.PROTECT, related_name="annotations"
    )
    annotation_value = models.ForeignKey(
        AnnotationValue, on_delete=models.PROTECT, related_name="annotations"
    )
    individual = models.ForeignKey(
        Individual, on_delete=models.CASCADE, related_name="annotations"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="annotations",
    )

    # Attributes - Mandatory
    created_at = models.DateTimeField(auto_now_add=True)

    # Attributes - Optional
    # Object Manager

    # Custom Properties

    # Methods
    def save(self, *args, **kwargs) -> None:

        if self.annotation_value not in self.annotation_attribute.values:
            raise ValueError(
                "The annotation value is not a valid option for this annotation attribute."
            )

        super().save(*args, **kwargs)

    # Meta and String
    class Meta:
        verbose_name = _("annotation")
        verbose_name_plural = _("annotations")
        constraints = [
            models.UniqueConstraint(
                fields=["user", "individual", "annotation_attribute"],
                name="unique_user_individual_annotation-attribute",
            )
        ]

    def __str__(self) -> str:
        return f"{self.annotation_attribute}->{self.annotation_attribute}"
