from django.contrib.gis import geos
from django.contrib.gis.db import models
from django.db.models import Q
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from treebeard.mp_tree import MP_Node

from ..utils.models import ParentManageableNodeMixin
from .managers import BoundaryManager, GeoLocatedManager, LocationManager

# Webs of interest:
#     - https://osm-boundaries.com/Map
#     - https://mapnik.org
#     - https://github.com/GeoNode/geonode
# As for now, only the concept of "Boundary" is contemplated in the DB schema.
# If multiple geometries are required someday, it would be better to group all columns into a
# JSONField and take an approach similar to OSM or django-geostore;
# which offers more flexibility in facing the problem.
# This solution is not still considered because having separate columns for each attribute is definitely more efficient
# and, at the moment, it is still not clear that other map node-like objects will be needed other
# than the concept of "Boundary".
#     - https://wiki.openstreetmap.org/wiki/Key:boundary
#     - https://wiki.openstreetmap.org/wiki/Map_features#Properties
#     - https://wiki.openstreetmap.org/w/images/5/58/OSM_DB_Schema_2016-12-13.svg  [SCHEMA]
#     - https://github.com/dcopm999/django-osm
#     - https://labs.mapbox.com/mapping/osm-data-model/
#     - https://github.com/Terralego/django-geostore


# This is a hierarchical system for dividing up the territory.


class BoundaryLayer(MP_Node, ParentManageableNodeMixin):
    class BoundaryType(models.TextChoices):
        ADMINISTRATIVE = "adm", _("Administrative")
        STATISTICAL = "sta", _("Statistical")

    # Relations
    boundary = models.ForeignKey(
        "Boundary",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="boundary_layers",
    )

    # Attributes - Mandatory
    boundary_type = models.CharField(
        max_length=3, choices=BoundaryType.choices, db_index=True
    )
    name = models.CharField(max_length=64)  # State, Province, NUTS3, etc
    level = models.PositiveSmallIntegerField(
        blank=True,
        db_index=True,
        help_text=_("Will use its depth inside the tree by default."),
    )

    # Attributes - Optional
    description = models.TextField(null=True, blank=True)

    # Object Manager
    # Custom Properties
    node_order_by = ["name"]  # Needed for django-treebeard

    # Methods
    def save(self, *args, **kwargs):

        try:
            if not self.is_root() and (root := self.get_root()):
                if self.boundary_type != root.boundary_type:
                    raise ValueError(
                        f"Only {root.boundary_type} boundary layer nodes are allowed in {root} tree."
                    )
        except self.__class__.DoesNotExist:
            # self.get_root() has not found any result.
            pass

        # Using depth as level default value
        if self._state.adding:
            # If creating
            if self.parent:
                # Getting from parent + 1
                self.level = self.parent.level + 1
            else:
                # Getting from node depth.
                # Substracting 1 since root depth starts from 1, while level start from 0.
                self.level = 0
        else:
            # If updating object
            if self.parent:
                # Checking that the current level is smaller than its parent
                if self.level <= self.parent.level:
                    raise ValueError(
                        "Level must be ascending order from parent to children."
                    )

        # Inherit the boundary owner from the parent.
        if self.parent and (p_boundary := self.parent.boundary):
            # NOTE: If someday we need to on self.boundary update, change the below update() method.
            self.boundary = p_boundary

        super().save(*args, **kwargs)

        # Make the descendants inherit same boundary as self.
        if self.boundary:
            # NOTE: update() does not call save method. So post_save, pre_save signals
            #       will not be called for these cases.
            self.get_descendants().update(boundary=self.boundary)

    # Meta and String
    class Meta:
        verbose_name = _("boundary layer")
        verbose_name_plural = _("boundary layers")
        ordering = ["boundary_type", "level", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["boundary", "boundary_type", "level"],
                name="unique_type-level_with_boundary",
            ),
            models.UniqueConstraint(
                fields=["boundary_type", "level"],
                condition=Q(boundary=None),
                name="unique_type-level_without_boundary",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.boundary_type}{self.level}: {self.name}"


class Boundary(MP_Node, ParentManageableNodeMixin):
    # Relations
    boundary_layer = models.ForeignKey(
        BoundaryLayer, on_delete=models.CASCADE, related_name="boundaries"
    )

    # Attributes - Mandatory
    code = models.CharField(max_length=16, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=128, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Attributes - Optional
    # Object Manager
    objects = BoundaryManager()

    # Custom Properties
    node_order_by = ["name"]  # Needed for django-treebeard

    @cached_property
    def geometry(self):
        return self.get_geometry()

    @property
    def boundary_type(self):
        return self.boundary_layer.boundary_type

    # Methods
    def get_geometry(self):
        try:
            # Query the BoundaryGeometry object and SELECT only
            # the geometry field.
            return BoundaryGeometry.objects.values_list("geometry", flat=True).get(
                boundary=self
            )
        except BoundaryGeometry.DoesNotExist:
            return None

    def save(self, *args, **kwargs) -> None:
        super().save(*args, **kwargs)

        # Updating geometry if it has been manually set.
        if "geometry" in self.__dict__.keys():
            # If geometry has changed or been called
            current_geometry = self.get_geometry()

            if not current_geometry or not self.geometry.equals(current_geometry):
                # If current geometry is not set OR is different.
                BoundaryGeometry.objects.update_or_create(
                    defaults={"geometry": self.geometry}, boundary=self
                )
                # Deleting cached property
                del self.geometry

    # Meta and String
    class Meta:
        verbose_name = _("Boundary")
        verbose_name_plural = _("Boundaries")
        constraints = [
            models.UniqueConstraint(
                fields=["boundary_layer", "code"], name="unique_boundarylayer_code"
            ),
        ]
        indexes = [models.Index(fields=["boundary_layer", "code"])]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class BoundaryGeometry(models.Model):
    """Stores the geometries of boundaries.

    We COULD have had a geometry column in the 'boundary' table, but geometries can get rather
    large, and loading them into memory every time you want to work with a bounadary
    is expensive.
    """

    # Relations
    boundary = models.OneToOneField(
        Boundary, on_delete=models.CASCADE, related_name="geometry_model"
    )

    # Attributes - Mandatory
    created_at = models.DateTimeField(auto_now_add=True)
    geometry = models.MultiPolygonField(geography=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Attributes - Optional
    # Object Manager
    # Custom Properties
    # Methods
    def save(self, *args, **kwargs):
        # if geom is a Polygon, make it into a MultiPolygon
        if self.geometry and isinstance(self.geometry, geos.Polygon):
            self.geometry = geos.MultiPolygon(self.geometry)

        if self._state.adding:
            # Link parent boundary with Location
            for loc in Location.objects.filter_by_polygon_intersection(
                self.geometry
            ).all():
                loc.boundaries.add(self.boundary)
                loc.save()

        super().save(*args, **kwargs)

    # Meta and String
    class Meta:
        verbose_name = _("boundary geometry")
        verbose_name_plural = _("boundary geometries")


class Location(models.Model):
    class LocationType(models.TextChoices):
        IN_VEHICLE = "VEH", _("Inside a vehicle.")
        IN_BUILDING = "BUI", _("Inside a building.")
        OUTDOORS = "OUT", _("Outdoors.")

    # Relations
    boundaries = models.ManyToManyField(Boundary, blank=True, related_name="locations")

    # Attributes - Mandatory
    point = models.PointField(geography=True)
    location_type = models.CharField(
        max_length=3, choices=LocationType.choices, null=True, blank=True
    )
    # TODO: add positional_accuray (The uncertainty in meters around the latitude and longitude.)

    # Attributes - Optional
    # Object Manager
    objects = LocationManager()

    # Custom Properties
    # Methods
    def _recompute_boundaries(self):
        # TODO check if signals are sent. otherwise, manually add/delete
        self.boundaries.set(Boundary.objects.reverse_geocoding(point=self.point).all())

    def save(self, *args, **kwargs) -> None:

        is_adding = self._state.adding

        super().save(*args, **kwargs)

        # On create: Adding boundaries to this location
        if is_adding:
            # TODO: make async
            self._recompute_boundaries()

    # Meta and String
    class Meta:
        verbose_name = _("location")
        verbose_name_plural = _("locations")

    def __str__(self) -> str:
        return (
            f"{str(self.point)} ({self.location_type})"
            if self.location_type
            else str(self.point)
        )


class GeoLocatedModel(models.Model):

    # Relations
    location = models.OneToOneField(
        Location,
        on_delete=models.PROTECT,
        related_name="+",
    )

    # Attributes - Mandatory

    # Attributes - Optional
    # Object Manager
    objects = GeoLocatedManager()

    # Custom Properties
    # Methods
    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.location.delete()

    # Meta and String
    class Meta:
        abstract = True
