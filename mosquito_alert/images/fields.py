import os

from django.db.models.fields.files import ImageFieldFile
from imagekit.models import ProcessedImageField as OriginalProcessedImageField
from imagekit.utils import generate, open_image, suggest_extension


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
        if exif := open_image(content).info.get("exif", None):
            spec.options["exif"] = exif
        # ADDED CODE END
        content = generate(spec)
        return super().save(new_name, content, save)


class ProcessedImageField(OriginalProcessedImageField):
    attr_class = ProcessedImageExifFieldFile
