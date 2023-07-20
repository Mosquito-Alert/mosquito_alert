from django.db.models import Manager
from treebeard.mp_tree import MP_NodeManager

from .querysets import BoundaryQuerySet, GeoLocatedModelQuerySet, LocationQuerySet


class BaseBoundaryManager(MP_NodeManager):
    def get_queryset(self):
        """Sets the custom queryset as the default."""
        # Get from BaseManager.get_queryset
        return self._queryset_class(model=self.model, using=self._db, hints=self._hints).order_by("path")


BoundaryManager = BaseBoundaryManager.from_queryset(BoundaryQuerySet)

LocationManager = Manager.from_queryset(LocationQuerySet)

GeoLocatedManager = Manager.from_queryset(GeoLocatedModelQuerySet)
