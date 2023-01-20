from modeltranslation.translator import TranslationOptions, translator

from .models import Boundary


class BoundaryTranslationOptions(TranslationOptions):
    fields = ("name",)


translator.register(Boundary, BoundaryTranslationOptions)
