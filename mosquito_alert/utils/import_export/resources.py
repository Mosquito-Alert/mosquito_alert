from collections import OrderedDict
from copy import deepcopy

from import_export import fields, resources, widgets
from modeltranslation.translator import translator


class ParentManageableModelResource(resources.ModelResource):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.fields.update(
            OrderedDict(
                [
                    (
                        "parent",
                        fields.Field(
                            attribute="parent",
                            column_name="parent__pk",
                            widget=widgets.ForeignKeyWidget(
                                model=self._meta.model, field="pk"
                            ),
                        ),
                    )
                ]
            )
        )

    def before_import(self, dataset, using_transactions, dry_run, **kwargs):

        if not (parent_column := self.fields["parent"].column_name) in dataset.headers:
            dataset.append_col([None] * len(dataset), header=parent_column)

        return super().before_import(dataset, using_transactions, dry_run, **kwargs)

    def after_import(self, dataset, result, using_transactions, dry_run, **kwargs):
        self._meta.model.fix_tree(fix_paths=False)

        return super().before_import(dataset, using_transactions, dry_run, **kwargs)


class TranslationModelResourceMixin:
    def __new__(cls, *args, **kwargs):

        new_class = super().__new__(cls)

        tranls_fields_dict = translator.get_options_for_model(
            new_class._meta.model
        ).fields

        # Getting those fields that have candidates
        tranls_fields_dict = dict(
            filter(
                lambda x: x[0] in new_class.fields.keys(), tranls_fields_dict.items()
            )
        )

        fields_to_append = []
        for field_name, field_trans in tranls_fields_dict.items():
            for t_field in list(field_trans):
                _field_instance = deepcopy(new_class.fields[field_name])
                _field_instance.attribute = t_field.name
                _field_instance.column_name = t_field.name

                fields_to_append.append((t_field.name, _field_instance))

        new_class.fields.update(OrderedDict(fields_to_append))

        return new_class

    def get_translation_candidates(self, fieldname) -> OrderedDict:

        posible_candidates = translator.get_options_for_model(self._meta.model).fields

        if fieldname not in posible_candidates.keys():
            return [
                None,
            ]

        name_candidates = [x.name for x in posible_candidates[fieldname]]

        return OrderedDict(
            filter(lambda x: x[0] in name_candidates, self.fields.items())
        )
