from django.db import models

from ...models import FlagModeratedModel


class DummyModel(models.Model):
    pass


class DummyFlagModeratedModel(FlagModeratedModel):
    pass
