from django.db import models
from django.utils.translation import gettext_lazy as _

from taggit.models import GenericUUIDTaggedItemBase, TaggedItemBase


class UUIDTaggedItem(GenericUUIDTaggedItemBase, TaggedItemBase):
    # NOTE: legacy since Report.version_UUID is still a charfield.
    object_id = models.CharField(
        max_length=36, verbose_name=_("object ID"), db_index=True
    )

    # See: https://django-taggit.readthedocs.io/en/stable/custom_tagging.html
    class Meta(GenericUUIDTaggedItemBase.Meta, TaggedItemBase.Meta):
        abstract = False
        db_table = "tigaserver_app_uuidtaggeditem"  # NOTE: migrate from old tigaserver_app, kept old name to avoid issues with custom third-party scripts that still uses the raw table name.
