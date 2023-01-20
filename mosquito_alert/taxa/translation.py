from modeltranslation.translator import TranslationOptions, translator

from .models import Taxon


class TaxonTranslationOptions(TranslationOptions):
    fields = ("common_name",)


translator.register(Taxon, TaxonTranslationOptions)
