import logging
from operator import itemgetter

from import_export import fields, widgets
from tqdm import tqdm

from ...utils.import_export.resources import (
    ParentManageableModelResource,
    TranslationModelResourceMixin,
)
from ..models import Boundary, BoundaryGeometry, BoundaryLayer
from .widgets import GeoWidget


class BoundaryResource(ParentManageableModelResource, TranslationModelResourceMixin):
    geometry = fields.Field(
        attribute="geometry",
        column_name="geometry",
        widget=GeoWidget(model_field=BoundaryGeometry._meta.get_field("geometry")),
    )

    boundary_layer = fields.Field(
        attribute="boundary_layer",
        column_name="boundary_layer__pk",
        widget=widgets.ForeignKeyWidget(model=BoundaryLayer, field="pk"),
    )

    def __init__(self, show_progess_bar=False, **kwargs):
        self.show_progess_bar = show_progess_bar
        super().__init__(**kwargs)

        self._parent_boundary_layer = None

    def _get_descriptor_name_from_row(self, row):
        descriptor = None
        # Getting all available fieldnames for 'name' (accepts translations).
        a_fields = [
            self.fields["name"].column_name,
        ] + list(self.get_translation_candidates(fieldname="name").keys())

        available_trans_columns = list(filter(lambda x: x in a_fields, row.keys()))

        if not available_trans_columns:
            return None

        row_values = itemgetter(*available_trans_columns)(row)
        if not isinstance(row_values, (list, tuple)):
            row_values = [row_values]
        available_trans_names = list(filter(lambda x: x is not None, row_values))

        # If available_trans_names, get first element or None
        if name := next(iter(available_trans_names), None):
            descriptor = name

        return descriptor

    def before_import(self, dataset, using_transactions, dry_run, **kwargs):
        self.progress_bar = tqdm(total=len(dataset)) if self.show_progess_bar else None

        boundary_layer = kwargs.pop("boundary_layer", None)
        name_fieldname = kwargs.pop("name_fieldname", None)
        code_fieldname = kwargs.pop("code_fieldname", None)

        if boundary_layer:
            dataset.append_col(
                [boundary_layer.pk] * len(dataset), header="boundary_layer__pk"
            )

            self._parent_boundary_layer = boundary_layer.parent

        if code_fieldname:
            self.fields["code"].column_name = code_fieldname
        if name_fieldname:
            self.fields["name"].column_name = name_fieldname

        super().before_import(dataset, using_transactions, dry_run, **kwargs)

    def before_import_row(self, row, row_number=None, **kwargs):
        if self.progress_bar:
            # Update progress_bar
            self.progress_bar.set_description(
                desc=self._get_descriptor_name_from_row(row=row) or str(row_number)
            )

        if not row[self.fields["parent"].column_name] and self._parent_boundary_layer:
            if row[self.fields["geometry"].column_name]:
                # Getting the geometry object from its value.
                geometry = self.fields["geometry"].clean(row)

                # Quering the DB to get parent boundaries (concentric).
                parent_boundary = (
                    Boundary.objects.fuzzy_reverse_polygon_geocoding(polygon=geometry)
                    .filter(boundary_layer=self._parent_boundary_layer)
                    .first_by_area()
                )

                if parent_boundary:
                    row[self.fields["parent"].column_name] = parent_boundary.pk
                else:
                    logging.warn(f"Not parent boundary found for row {row}")

        super().before_import_row(row, row_number=row_number, **kwargs)

    def after_import_row(self, row, row_result, row_number=None, **kwargs):
        if self.progress_bar:
            self.progress_bar.update()
        super().after_import_row(row, row_result, row_number=row_number, **kwargs)

    class Meta:
        model = Boundary
        fields = ["id", "code", "name"]
        use_bulk = False  # DO NOT CHANGE
        use_transactions = True
