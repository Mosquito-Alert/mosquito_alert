from modeltranslation.translator import TranslationOptions, translator

from .models import Disease


class DiseaseTranslationOptions(TranslationOptions):
    fields = ("name",)


translator.register(Disease, DiseaseTranslationOptions)
