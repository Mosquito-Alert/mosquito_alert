from typing import Any

from django.db import models

from .querysets import FlagModeratedQueryset, FlagQuerySet

FlagManager = models.Manager.from_queryset(FlagQuerySet)

FlagModeratedManager = models.Manager.from_queryset(FlagModeratedQueryset)


class FlagInstanceManager(models.Manager):
    def create(self, model_obj: models.Model = None, **kwargs: Any) -> Any:
        from .models import Flag

        if model_obj and "flag" not in kwargs:
            kwargs["flag"] = Flag.objects.create(content_object=model_obj)

        return super().create(**kwargs)
