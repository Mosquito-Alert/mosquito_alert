import os

from django.db.models.fields.files import ImageFieldFile
from imagekit.models import ProcessedImageField
from imagekit.utils import generate, open_image, suggest_extension


class ProcessedImageExifFieldFile(ImageFieldFile):
    def save(self, name, content, save=True):
        # COPIED FROM ProcessedImageFieldFile
        filename, ext = os.path.splitext(name)
        spec = self.field.get_spec(source=content)
        ext = suggest_extension(name, spec.format)
        new_name = f"{filename}{ext}"
        # ADDED CODE START
        if not spec.options:
            spec.options = {}
        spec.options["exif"] = open_image(content).info.get("exif", None)
        # ADDED CODE END
        content = generate(spec)
        return super().save(new_name, content, save)


class ProcessedImageField(ProcessedImageField):
    attr_class = ProcessedImageExifFieldFile
