from django.contrib import admin
from django.contrib.gis.admin.options import GeoModelAdminMixin
from django.utils.translation import gettext_lazy as _
from django_admin_inline_paginator.admin import TabularInlinePaginated
from modeltranslation.admin import TranslationAdmin, TranslationTabularInline
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from ..utils.forms import (
    AllowOnlyNodesFromSameTreeFormMixin,
    ParentManageableMoveNodeForm,
)
from .import_export.admin import ShapefileImportMixin
from .import_export.resources import BoundaryResource
from .models import Boundary, BoundaryGeometry, BoundaryLayer


class MoveNodeFormOnlyNodesFromSameTree(
    AllowOnlyNodesFromSameTreeFormMixin, ParentManageableMoveNodeForm
):
    pass


class BoundaryGeometryInlineAdmin(GeoModelAdminMixin, admin.StackedInline):
    model = BoundaryGeometry
    fields = ("geometry",)
    can_delete = False

    gis_widget_kwargs = {
        "attrs": {
            "disabled": True  # Removing the 'Delete all Features' button from the map.
        }
    }


class BoundaryAdmin(ShapefileImportMixin, TreeAdmin, TranslationAdmin):

    # Custom filters
    class ObjectsWithConflicts(admin.SimpleListFilter):
        title = _("conflict presence")
        parameter_name = "conflicts"

        def lookups(self, request, model_admin):
            return ((True, _("Yes")), (False, _("No")))

        def queryset(self, request, queryset):
            if self.value() == "True":
                queryset = queryset.have_boundary_layer_conflicts()
            return queryset

    # For TreeAdmin
    form = movenodeform_factory(Boundary, form=MoveNodeFormOnlyNodesFromSameTree)

    # For ShapefileImportMixin
    resource_classes = [
        BoundaryResource,
    ]

    def has_import_permission(self, request):
        """
        Returns whether a request has import permission.
        """
        return super().has_add_permission(request)

    # Default admin
    inlines = [
        BoundaryGeometryInlineAdmin,
    ]

    search_fields = ("name", "code")
    list_display = ("__str__", "boundary_layer")
    list_filter = (
        "boundary_layer__boundary_type",
        "boundary_layer",
        "created_at",
        "updated_at",
        "depth",
        ObjectsWithConflicts,
    )

    # See MoveNodeForm for '_position', '_ref_node_id'
    readonly_fields = ("boundary_type",)
    fields = (
        ("_position", "_ref_node_id"),
        ("boundary_layer", "boundary_type"),
        "code",
        "name",
    )

    @admin.display()
    def boundary_type(self, obj):
        return obj.boundary_layer.get_boundary_type_display()

    def has_add_permission(self, request):
        return False


class BoundaryInlineAdmin(TabularInlinePaginated, TranslationTabularInline):
    model = Boundary

    show_change_link = True

    # Excluding tree-related fields.
    fields = ("name", "code")
    exclude = ("path", "depth", "numchild")
    ordering = ("name",)

    # For TabularInlinePaginated
    per_page = 20

    def has_add_permission(self, request, obj):
        return False


class BoundaryLayerAdmin(TreeAdmin):

    autocomplete_fields = ("boundary",)

    search_fields = ("name",)
    inlines = [
        BoundaryInlineAdmin,
    ]

    form = movenodeform_factory(BoundaryLayer, form=MoveNodeFormOnlyNodesFromSameTree)

    fields = (
        ("_position", "_ref_node_id"),
        "boundary",
        "name",
        ("level", "boundary_type"),
        "description",
    )

    list_display = ("name", "boundary_type", "level", "boundary")
    list_filter = (
        "boundary_type",
        "level",
        ("boundary", admin.RelatedOnlyFieldListFilter),
    )

    def get_readonly_fields(self, request, obj=None):
        """
        Hook for specifying custom readonly fields.
        """
        results = list(super().get_readonly_fields(request, obj=obj))

        if obj and obj.parent and obj.parent.boundary:
            # make boundary readonly if it has a parent with and set boundary.
            # results.append('boundary')
            pass

        return tuple(results)

    def get_form(self, request, obj, change, **kwargs):
        form = super().get_form(request, obj, change, **kwargs)
        if obj:
            form.base_fields["boundary"].queryset = Boundary.objects.filter(
                boundary_layer__boundary_type=obj.boundary_type
            ).all()

        return super().get_form(request, obj, change, **kwargs)


admin.site.register(Boundary, BoundaryAdmin)
admin.site.register(BoundaryLayer, BoundaryLayerAdmin)
