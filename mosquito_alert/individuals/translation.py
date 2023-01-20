from modeltranslation.translator import TranslationOptions, translator

from .models import AnnotationAttribute, AnnotationValue


class AnnotationValueTranslationOptions(TranslationOptions):
    fields = ("label",)


class AnnotationAttributeTranslationOptions(TranslationOptions):
    fields = ("label",)


translator.register(AnnotationValue, AnnotationValueTranslationOptions)
translator.register(AnnotationAttribute, AnnotationAttributeTranslationOptions)
