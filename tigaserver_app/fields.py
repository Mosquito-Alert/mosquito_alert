import os
from PIL import Image, ImageOps, ExifTags

from django.db.models.fields.files import ImageFieldFile

from rest_framework import serializers

from imagekit.models import ProcessedImageField as OriginalProcessedImageField
from imagekit.utils import generate, open_image, suggest_extension

class NullableTimeZoneDatetimeField(serializers.DateTimeField):
    def enforce_timezone(self, value):
        return value


class AutoTimeZoneDatetimeField(NullableTimeZoneDatetimeField):
    # NOTE: to be used when inheriting AutoTimeZoneSerializerMixin
    pass

class ProcessedImageExifFieldFile(ImageFieldFile):
    def save(self, name, content, save=True):
        # COPIED FROM OriginalProcessedImageField
        filename, ext = os.path.splitext(name)
        spec = self.field.get_spec(source=content)
        ext = suggest_extension(name, spec.format)
        new_name = f"{filename}{ext}"
        # ADDED CODE START
        if not spec.options:
            spec.options = {}
        if exif := open_image(content).getexif():
            # Remove tags related to size and format if they exist
            tags_to_remove = ["ImageWidth", "ImageLength"]
            for tag, value in ExifTags.TAGS.items():
                if value in tags_to_remove:
                    exif.pop(tag, None)
            spec.options["exif"] = exif
        # ADDED CODE END
        content = generate(spec)
        return super().save(new_name, content, save)

    def _get_image_dimensions(self):
        if not hasattr(self, "_dimensions_cache"):
            close = self.closed
            self.open()
            img = Image.open(self.file)

            img_trans = ImageOps.exif_transpose(img)
            self._dimensions_cache = img_trans.size
            img_trans.close()

            if close:
                self.close()

        return self._dimensions_cache


class ProcessedImageField(OriginalProcessedImageField):
    attr_class = ProcessedImageExifFieldFile