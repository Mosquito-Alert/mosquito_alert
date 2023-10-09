from django.contrib.gis import geos
from django.contrib.gis.db import models
from django.db.models import Q
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django_lifecycle import (
    AFTER_CREATE,
    AFTER_UPDATE,
    BEFORE_CREATE,
    BEFORE_UPDATE,
    LifecycleModel,
    LifecycleModelMixin,
    hook,
)
from treebeard.mp_tree import MP_Node

from mosquito_alert.utils.models import ParentManageableNodeMixin, TimeStampedModel

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


class BoundaryLayer(ParentManageableNodeMixin, LifecycleModelMixin, MP_Node):
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
    boundary_type = models.CharField(max_length=3, choices=BoundaryType.choices, db_index=True)
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
    @hook(AFTER_UPDATE, when="boundary")
    def update_descendants_boundaries(self):
        # NOTE: update() does not call save method. So post_save, pre_save signals
        #       will not be called for these cases.
        self.get_descendants().update(boundary=self.boundary)

    def save(self, *args, **kwargs):
        try:
            if not self.is_root() and (root := self.get_root()):
                if self.boundary_type != root.boundary_type:
                    raise ValueError(f"Only {root.boundary_type} boundary layer nodes are allowed in {root} tree.")
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
                    raise ValueError("Level must be ascending order from parent to children.")

        # Inherit the boundary owner from the parent.
        if self.parent and (p_boundary := self.parent.boundary):
            # NOTE: If someday we need to on self.boundary update, change the below update() method.
            self.boundary = p_boundary

        super().save(*args, **kwargs)

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


class Boundary(ParentManageableNodeMixin, TimeStampedModel, MP_Node):
    # Relations
    boundary_layer = models.ForeignKey(BoundaryLayer, on_delete=models.CASCADE, related_name="boundaries")

    # Attributes - Mandatory
    code = models.CharField(max_length=16, db_index=True)
    name = models.CharField(max_length=128, db_index=True)

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
            return BoundaryGeometry.objects.values_list("geometry", flat=True).get(boundary=self)
        except BoundaryGeometry.DoesNotExist:
            return None

    def save(self, *args, **kwargs) -> None:
        super().save(*args, **kwargs)

        # Updating geometry if it has been manually set.
        if "geometry" in self.__dict__.keys():
            old_geometry = self.get_geometry()
            new_geometry = self.__dict__["geometry"]

            if new_geometry:
                if old_geometry:
                    if not new_geometry.equals(old_geometry):
                        geom_model = self.geometry_model
                        geom_model.geometry = new_geometry
                        geom_model.save()

                        # Deleting cached property
                        del self.geometry
                else:
                    BoundaryGeometry.objects.create(boundary=self, geometry=new_geometry)
                    # Deleting cached property
                    del self.geometry
            else:
                BoundaryGeometry.objects.filter(boundary=self).delete()
                # Deleting cached property
                del self.geometry

    # Meta and String
    class Meta(TimeStampedModel.Meta):
        verbose_name = _("Boundary")
        verbose_name_plural = _("Boundaries")
        constraints = TimeStampedModel.Meta.constraints + [
            models.UniqueConstraint(fields=["boundary_layer", "code"], name="unique_boundarylayer_code"),
        ]
        indexes = [models.Index(fields=["boundary_layer", "code"])]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class BoundaryGeometry(LifecycleModel, TimeStampedModel):
    """Stores the geometries of boundaries.

    We COULD have had a geometry column in the 'boundary' table, but geometries can get rather
    large, and loading them into memory every time you want to work with a bounadary
    is expensive.
    """

    # Relations
    boundary = models.OneToOneField(
        Boundary,
        on_delete=models.CASCADE,
        related_name="geometry_model",
        primary_key=True,
    )

    # Attributes - Mandatory
    geometry = models.MultiPolygonField(geography=False)

    # Attributes - Optional
    # Object Manager
    # Custom Properties
    # Methods
    def __init__(self, *args, **kwargs):
        # NOTE: __init__ signature can not be changed
        # See: https://docs.djangoproject.com/en/dev/ref/models/instances/#django.db.models.Model
        geometry = kwargs.get("geometry", None)
        if geometry and isinstance(geometry, geos.Polygon):
            kwargs.update({"geometry": geos.MultiPolygon(geometry)})
        super().__init__(*args, **kwargs)

    @hook(BEFORE_CREATE)
    @hook(BEFORE_UPDATE, when="geometry", has_changed=True)
    def _validate_geometry(self):
        # if geom is a Polygon, make it into a MultiPolygon
        if self.geometry:
            if self.geometry.empty:
                raise ValueError("The new geometry can not be empty.")

    @hook(AFTER_UPDATE, when="geometry", has_changed=True)
    def update_linked_location(self):
        # Get Location objects linked to this Boundary, and which point now rest outside
        # the boundary.
        loc_qs = Location.objects.filter(boundaries=self.boundary).filter_by_polygon_intersection(
            polygon=self.geometry, negate=True
        )
        for loc in loc_qs.all():
            loc.boundaries.remove(self.boundary)

        self._link_boundary_to_location()

    @hook(AFTER_CREATE)
    def _link_boundary_to_location(self):
        loc_qs = Location.objects.filter_by_polygon_intersection(polygon=self.geometry).exclude(
            boundaries=self.boundary
        )
        for loc in loc_qs.all():
            loc.boundaries.add(self.boundary)

    # Meta and String
    class Meta(TimeStampedModel.Meta):
        verbose_name = _("boundary geometry")
        verbose_name_plural = _("boundary geometries")


class Location(LifecycleModel):
    class LocationType(models.TextChoices):
        IN_VEHICLE = "VEH", _("Inside a vehicle.")
        IN_BUILDING = "BUI", _("Inside a building.")
        OUTDOORS = "OUT", _("Outdoors.")

    # Relations
    boundaries = models.ManyToManyField(Boundary, blank=True, related_name="locations")

    # Attributes - Mandatory
    point = models.PointField(geography=False)
    location_type = models.CharField(max_length=3, choices=LocationType.choices, null=True, blank=True)
    # TODO: add positional_accuray (The uncertainty in meters around the latitude and longitude.)

    # Attributes - Optional
    # Object Manager
    objects = LocationManager()

    # Custom Properties
    # Methods
    @hook(AFTER_CREATE)
    @hook(AFTER_UPDATE, when="point", has_changed=True)
    def update_linked_boundaries(self):
        self.boundaries.set(Boundary.objects.reverse_geocoding(point=self.point).all())

    # Meta and String
    class Meta:
        verbose_name = _("location")
        verbose_name_plural = _("locations")

    def __str__(self) -> str:
        result = f"{str(self.point.coords)}"
        if self.location_type:
            result = result + f" ({self.location_type})"
        return result


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
