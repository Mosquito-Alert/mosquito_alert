import os
import uuid
from pathlib import Path

from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from flag.models import Flag
from imagekit.processors import ResizeToFit, Transpose
from PIL import ExifTags, Image, TiffImagePlugin

from .fields import ProcessedImageField


def image_upload_to(instance, filename):
    # Since we define the format in imagekit processors,
    # a recommended extension is already found in the filename
    _, ext = os.path.splitext(filename)

    # Checking if filename is already a valid UUID.
    # Using it if it is valid.
    try:
        uuid_str = uuid.UUID(hex=Path(filename).stem, version=4)
    except ValueError:
        # Creating a new uuid
        uuid_str = uuid.uuid4()
    # No need to add the extension. ProcessedPictureFieldFile already does.
    return os.path.join("images", f"{uuid_str}{ext}")


class Photo(models.Model):

    # Relations
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="photos",
        on_delete=models.SET_NULL,
    )
    flags = GenericRelation(Flag)

    # Attributes - Mandatory
    image = ProcessedImageField(
        upload_to=image_upload_to,
        processors=[Transpose(), ResizeToFit(height=720, upscale=False)],
        format="WEBP",
        options={"quality": 85},
    )
    created_at = models.DateTimeField(default=timezone.now, blank=True)

    # Attributes - Optional

    # Object Manager
    # Custom Properties
    @cached_property
    def exif_dict(self):
        # NOTE: this information is user-sensitive. Consider it private, never expose it in views/api.
        img = Image.open(self.image)
        img_exif = img.getexif()
        return {
            ExifTags.TAGS[key]: val
            for key, val in img_exif.items()
            if type(val) not in [bytes, TiffImagePlugin.IFDRational]
        }

    # Methods

    # Meta and String
    class Meta:
        verbose_name = _("photo")
        verbose_name_plural = _("photos")
        ordering = ["-created_at"]
        permissions = [
            ("view_exif", _("Can view exif metadata")),
        ]

    def __str__(self):
        return Path(self.image.name).stem
