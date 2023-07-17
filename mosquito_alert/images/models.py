import os
import uuid
from pathlib import Path

from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from flag.models import Flag
from imagekit.processors import ResizeToFit
from PIL import ExifTags, Image

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
    # NOTE: If a processor to autorotate is used, check that
    #       EXIF orientation is modified accordingly.
    #       Check PIL.ImageOps.exif_transpose()
    image = ProcessedImageField(
        upload_to=image_upload_to,
        processors=[ResizeToFit(height=720, upscale=False)],
        format="WEBP",
        options={"quality": 85},
    )
    created_at = models.DateTimeField(auto_now_add=True)
    # TODO: license + attributions

    # Attributes - Optional

    # Object Manager
    # Custom Properties
    @cached_property
    def exif_dict(self):
        # NOTE: this information is user-sensitive. Consider it private, never expose it in views/api.
        info = Image.open(self.image)._getexif()
        if not info:
            return {}

        exif_data = {}
        for tag, value in info.items():
            decoded = str(ExifTags.TAGS.get(tag, tag))
            if decoded == "GPSInfo":
                gps_data = {}
                for gps_tag in value:
                    sub_decoded = ExifTags.GPSTAGS.get(gps_tag, gps_tag)
                    gps_data[sub_decoded] = str(value[gps_tag])
                exif_data[decoded] = gps_data
            else:
                exif_data[decoded] = str(value)

        return exif_data

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
        return os.path.basename(self.image.name)
