from abc import ABC
from contextlib import nullcontext as does_not_raise
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, models

from mosquito_alert.utils.tests.test_models import AbstractDjangoModelTestMixin, BaseTestTimeStampedModel

from ...utils.tests.utils import func_in_race_condition_test
from ..models import BasePhotoAnnotationTask, BaseShape
from ..shapes import Rectangle


####################
# Task
####################
class BaseTestBaseTask(BaseTestTimeStampedModel, ABC):
    # fields
    def test_is_completed_can_not_be_null(self):
        assert not self.model._meta.get_field("is_completed").null

    def test_is_completed_is_default_False(self):
        assert not self.model._meta.get_field("is_completed").default

    # methods
    def test__run_on_is_completed_changes_is_called_on_change(self):
        obj = self.factory_cls()

        with patch.object(obj, "_run_on_is_completed_changes", return_value=None) as mocked_method:
            with patch.object(obj, "_get_is_completed_value", return_value=not obj.is_completed):
                obj.save()

            mocked_method.assert_called_once()

    def test_update_is_completed_sets_value_with__get_is_completed_value_result(self):
        obj = self.factory_cls.build()

        assert not obj.is_completed

        with patch.object(obj, "_get_is_completed_value", return_value=True) as mocked_method:
            obj.update_is_completed()

            mocked_method.assert_called_once()
            assert obj.is_completed

    def test_save_does_not_call_update_is_completed_if_adding(self):
        obj = self.factory_cls.build()

        with patch("django.db.models.Model.save", return_value=None):
            with patch.object(obj, "update_is_completed", return_value=None) as mocked_method:
                obj.save()
                mocked_method.assert_not_called()

    def test_save_calls_update_is_completed_if_update_fields_is_defined(self):
        obj = self.factory_cls()

        with patch.object(obj, "update_is_completed", return_value=None) as mocked_method:
            obj.save(update_fields=["is_completed"])
            mocked_method.assert_called_once()

    def test_save_calls_update_is_completed(self):
        obj = self.factory_cls()

        with patch.object(obj, "update_is_completed", return_value=None) as mocked_method:
            obj.save()
            mocked_method.assert_called_once()


class BaseTestBaseAnnotationTask(BaseTestBaseTask, ABC):
    _COUNTER_FIELDS = ["total_annotations", "skipped_annotations", "total_predictions"]

    _COUNTER_FIELDS_TO_INCREASE_FUNCTIONS = {
        "total_annotations": "increase_annotation_counter",
        "skipped_annotations": "increase_skipped_annotation_counter",
        "total_predictions": "increase_prediction_counter",
    }

    _COUNTER_FIELDS_TO_DECREASE_FUNCTIONS = {
        "total_annotations": "decrease_annotation_counter",
        "skipped_annotations": "decrease_skipped_annotation_counter",
        "total_predictions": "decrease_prediction_counter",
    }

    def _test_counter_func_in_race_condition(self, func_name, field_name, inital_value, inc_value):
        # IMPORTANT: all functions calling this must have the decorator @pytest.mark.django_db(transaction=True)
        obj = self.factory_cls(**{field_name: inital_value})

        func_in_race_condition_test(
            obj=obj,
            func=lambda: getattr(obj, func_name)(),
            validation_func=lambda: getattr(obj, field_name) == inital_value + inc_value,
        )

    # fields
    @pytest.mark.parametrize("field_name", _COUNTER_FIELDS)
    def test_counter_field_can_not_be_None(self, field_name):
        with pytest.raises(IntegrityError, match=r"not-null constraint"):
            _ = self.factory_cls(**{field_name: None})

    @pytest.mark.parametrize("field_name", _COUNTER_FIELDS)
    def test_counter_field_can_not_be_negative(self, field_name):
        with pytest.raises(IntegrityError, match=r"check constraint"):
            self.factory_cls(**{field_name: -1})

    @pytest.mark.parametrize("field_name", _COUNTER_FIELDS)
    def test_counter_field_defaults_to_0(self, field_name):
        obj = self.factory_cls()
        assert getattr(obj, field_name) == 0

    @pytest.mark.parametrize("field_name", _COUNTER_FIELDS)
    def test_counter_field_can_not_be_editable(self, field_name):
        assert not self.model._meta.get_field(field_name).editable

    @pytest.mark.parametrize("field_name", _COUNTER_FIELDS)
    def test_counter_fields_are_indexed(self, field_name):
        assert self.model._meta.get_field(field_name).db_index

    # methods
    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize(
        "func_name, field_name", [(v, k) for k, v in _COUNTER_FIELDS_TO_INCREASE_FUNCTIONS.items()]
    )
    def test_increase_counter_func_in_race_condition(self, func_name, field_name):
        self._test_counter_func_in_race_condition(
            func_name=func_name, field_name=field_name, inital_value=0, inc_value=1
        )

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize(
        "func_name, field_name", [(v, k) for k, v in _COUNTER_FIELDS_TO_DECREASE_FUNCTIONS.items()]
    )
    def test_decrease_counter_func_in_race_condition(self, func_name, field_name):
        self._test_counter_func_in_race_condition(
            func_name=func_name, field_name=field_name, inital_value=10, inc_value=-1
        )


class BaseTestBasePhotoAnnotationTask(BaseTestBaseAnnotationTask, ABC):
    # fields
    def test_photo_can_not_be_null(self):
        with pytest.raises(IntegrityError, match=r"not-null constraint"):
            _ = self.factory_cls(photo=None)

    def test_photo_on_delete_cascade(self):
        _on_delete = self.model._meta.get_field("photo").remote_field.on_delete
        assert _on_delete == models.CASCADE


class BaseTestBaseAnnotation(AbstractDjangoModelTestMixin, ABC):
    # fields
    def test__str__(self):
        obj = self.factory_cls()
        assert str(obj) == f"{obj.label}"


class BaseTestBasePhotoAnnotation(BaseTestBaseAnnotation, ABC):
    # fields
    def test_task_field_is_fk_of_subclass(self):
        assert issubclass(self.model.task.field.related_model, BasePhotoAnnotationTask)


class BaseTestBaseShape(AbstractDjangoModelTestMixin, ABC):
    # fields
    def test_shape_type_can_not_be_null(self):
        assert not self.model._meta.get_field("shape_type").null

    def test_points_can_not_be_null(self):
        assert not self.model._meta.get_field("points").null

    @pytest.mark.parametrize(
        "points, expected_raise",
        [
            ([[0, 0], [0.5, 0.5]], does_not_raise()),
            ([[0, 0], [0.5, 0.5], [0.5, 0.5], [0.5, 0.5]], does_not_raise()),
            (
                [
                    [0, 0],
                ],
                does_not_raise(),
            ),
            ([[0, 0, 0], [0.5, 0.5, 0.5]], pytest.raises(ValidationError)),
            ([[0, 0], [1.1, 1.1]], pytest.raises(ValidationError)),
            ([[-0.1, -0.1], [0.5, 0.5]], pytest.raises(ValidationError)),
        ],
    )
    def test_points_is_flatten_list_of_points(self, points, expected_raise):
        # Mocking clean() to only force exhaustive ArrayField validation, without
        # taking into account the shape_type.
        with patch(f"{self.model.__module__}.{self.model.__name__}.clean", return_value=None):
            with expected_raise:
                excluded_field_names = [x.name for x in self.model._meta.fields]
                excluded_field_names.remove("points")
                self.factory_cls.build(points=points).full_clean(exclude=excluded_field_names)

    # properties
    @pytest.mark.parametrize(
        "shape_type, points, expected_result",
        [(BaseShape.ShapeType.RECTANGLE, [[0, 0], [0.5, 0.5]], Rectangle(points=[[0, 0], [0.5, 0.5]]))],
    )
    def test_shape_property(self, shape_type, points, expected_result):
        obj = self.factory_cls(shape_type=shape_type, points=points)
        assert obj.shape == expected_result

    def test_shape_setter(self):
        obj = self.factory_cls(shape_type=BaseShape.ShapeType.RECTANGLE, points=[[0, 0], [0.5, 0.5]])

        obj.shape = Rectangle(points=[[0, 0], [1, 1]])

        assert obj.points == ((0, 0), (1, 1))
        assert obj.shape_type == BaseShape.ShapeType.RECTANGLE

    # methods
    @pytest.mark.parametrize(
        "points, shape_type, expected_raise",
        [
            ([[0, 0], [0.5, 0.5]], BaseShape.ShapeType.RECTANGLE, does_not_raise()),
            ([[0, 0]], BaseShape.ShapeType.RECTANGLE, pytest.raises(ValidationError)),
            ([[]], BaseShape.ShapeType.RECTANGLE, pytest.raises(ValidationError)),
            ([[0, 0], [0.5, 0.5], [0.5, 0.5]], BaseShape.ShapeType.RECTANGLE, pytest.raises(ValidationError)),
        ],
    )
    def test_clean(self, points, shape_type, expected_raise):
        with expected_raise:
            _ = self.factory_cls(points=points, shape_type=shape_type).clean()

    def test_clean_is_called_on_create(self):
        with patch(f"{self.model.__module__}.{self.model.__name__}.clean", return_value=None) as mock_method:
            _ = self.factory_cls()

            mock_method.assert_called_once()

    def test_clean_is_called_on_save(self):
        obj = self.factory_cls()

        with patch.object(obj, "clean", return_value=None) as mock_method:
            obj.save()

            mock_method.assert_called_once()

    def test_points_is_validated_on_save(self):
        obj = self.factory_cls()

        with patch.object(obj, "full_clean", return_value=None) as mock_method:
            obj.save()

            excluded_field_names = [x.name for x in self.model._meta.fields]
            excluded_field_names.remove("points")
            mock_method.assert_called_once_with(exclude=excluded_field_names)
