from taggit.models import GenericUUIDTaggedItemBase, TaggedItemBase


class UUIDTaggedItem(GenericUUIDTaggedItemBase, TaggedItemBase):
    # See: https://django-taggit.readthedocs.io/en/stable/custom_tagging.html
    class Meta(GenericUUIDTaggedItemBase.Meta, TaggedItemBase.Meta):
        abstract = False
