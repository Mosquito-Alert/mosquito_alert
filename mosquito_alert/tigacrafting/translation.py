from modeltranslation.translator import TranslationOptions, register

from .models import Taxon

@register(Taxon)
class TaxonTranslationOptions(TranslationOptions):
    fields = ("common_name",)