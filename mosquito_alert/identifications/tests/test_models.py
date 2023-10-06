import random
from abc import ABC, abstractmethod
from contextlib import nullcontext as does_not_raise
from datetime import timedelta
from decimal import Decimal
from unittest.mock import Mock, PropertyMock, call, patch

import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import DatabaseError, IntegrityError, models
from django.utils import timezone

from mosquito_alert.annotations.models import BaseShape
from mosquito_alert.annotations.tests.test_models import (
    BaseTestBaseAnnotation,
    BaseTestBasePhotoAnnotationTask,
    BaseTestBaseShape,
    BaseTestBaseTask,
)
from mosquito_alert.images.tests.factories import PhotoFactory
from mosquito_alert.individuals.tests.factories import IndividualFactory
from mosquito_alert.taxa.models import Taxon
from mosquito_alert.taxa.tests.factories import TaxonFactory
from mosquito_alert.users.tests.factories import UserFactory
from mosquito_alert.utils.tests.test_models import BaseTestObservableMixin, BaseTestTimeStampedModel

from ..models import (
    BaseClassification,
    BasePhotoIdentification,
    BaseTaskResult,
    ExternalIdentification,
    IndividualIdentificationTask,
    IndividualIdentificationTaskResult,
    PhotoIdentificationTask,
    PhotoIdentificationTaskResult,
    Prediction,
    TaxonClassificationCandidate,
    UserIdentification,
    classification_has_changed,
    identification_task_has_changed,
)
from ..prob_tree import TaxonProbNode
from ..settings import NUM_USER_IDENTIFICATIONS_TO_COMPLETE
from .factories import (
    DummyClassificationFactory,
    ExternalIdentificationFactory,
    IndividualIdentificationTaskFactory,
    IndividualIdentificationTaskResultFactory,
    PhotoIdentificationTaskFactory,
    PhotoIdentificationTaskResultFactory,
    PredictionFactory,
    TaxonClassificationCandidateFactory,
    TaxonProbNodeFactory,
    UserIdentificationFactory,
)


#############################
class BaseTestBaseTaxonAnnotation(BaseTestObservableMixin, BaseTestBaseAnnotation, ABC):
    model = None
    factory_cls = None

    @pytest.mark.parametrize("fieldname", ["label", "probability"])
    def test__notify_changes_is_called_on_field_change(self, fieldname):
        super().assert__notify_changes_is_called_on_field_change(fieldname)

    # fields
    def test_label_cls_is_taxon(self):
        assert self.model.label.field.related_model is Taxon

    def test_label_can_not_be_null(self):
        assert not self.model._meta.get_field("label").null

    def test_label_is_protected_on_delete(self):
        _on_delete = self.model._meta.get_field("label").remote_field.on_delete
        assert _on_delete == models.PROTECT

    def test_label_choices_is_gte_taxon_rank_class(self):
        limit_choices_dict = self.model._meta.get_field("label").remote_field.limit_choices_to
        assert limit_choices_dict["rank__gte"] == Taxon.TaxonomicRank.CLASS

    def test_probability_can_not_be_null(self):
        assert not self.model._meta.get_field("probability").null

    def test_probability_max_digits_decimal_places(self):
        probability_field = self.model._meta.get_field("probability")

        assert probability_field.max_digits == 7
        assert probability_field.decimal_places == 6

    @pytest.mark.parametrize(
        "value, expected_raise",
        [
            (-0.01, pytest.raises(IntegrityError)),
            (0, does_not_raise()),
            (0.5, does_not_raise()),
            (1, does_not_raise()),
            (1.01, pytest.raises(IntegrityError)),
        ],
    )
    def test_probability_between_0_and_1(self, value, expected_raise):
        obj = self.factory_cls()
        obj.probability = value

        with expected_raise:
            obj.save()

    # object manager
    def test_default_queryset_add_label_select_related(self):
        assert "label" in self.model.objects.get_queryset().query.select_related.keys()

    # properties
    def test_to_tree_node_return_TaxonProbNode(self, taxon_root):
        obj = self.factory_cls(label=taxon_root, probability=1)

        tree_node = obj.to_tree_node
        assert isinstance(tree_node, TaxonProbNode)

        assert tree_node.to_dict == TaxonProbNode(taxon=taxon_root, probability=1).to_dict

    def test_property_taxon_return_label(self):
        obj = self.factory_cls()

        assert obj.taxon == obj.label

    def test_taxon_setters_sets_label(self, taxon_root, taxon_specie):
        obj = self.factory_cls(label=taxon_root)

        obj.taxon = taxon_specie
        obj.save()

        assert obj.label == taxon_specie

    # methods
    def test__notify_changes_only_sends_signal_if_fields_changed_arg_is_not_empty(self):
        obj = self.factory_cls()

        with patch.object(classification_has_changed, "send", return_value=None) as mocked_signal:
            obj._notify_changes(fields_changed=[])

            mocked_signal.assert_not_called()

    def test__notify_changes_send_classification_has_changed_signal_only_if_fields_in_NOTIFY_ON_FIELD_CHANGE(self):
        obj = self.factory_cls()

        fake_fields = ["fake_field1", "fake_field2"]
        fields_changed = fake_fields + self.model.NOTIFY_ON_FIELD_CHANGE

        with patch.object(classification_has_changed, "send", return_value=None) as mocked_signal:
            obj._notify_changes(fields_changed=fields_changed)

            mocked_signal.assert_called_once_with(
                sender=obj.__class__, instance=obj, fields_changed=self.model.NOTIFY_ON_FIELD_CHANGE
            )

    # meta
    def test__str__(self, taxon_root):
        obj = self.factory_cls(label=taxon_root, probability=1)
        assert str(obj) == f"{taxon_root} (p=1)"


@pytest.mark.django_db
class TestTaxonClassificationCandidate(BaseTestBaseTaxonAnnotation, BaseTestTimeStampedModel):
    model = TaxonClassificationCandidate
    factory_cls = TaxonClassificationCandidateFactory

    def test__notify_changes_is_called_on_is_seed_change(self):
        super().assert__notify_changes_is_called_on_field_change(fieldname="is_seed")

    # fields
    def test_content_type_can_not_be_null(self):
        assert not self.model._meta.get_field("content_type").null

    def test_content_type_on_delete_is_cascade(self):
        assert self.model._meta.get_field("content_type").remote_field.on_delete == models.CASCADE

    def test_content_type_only_subclass_of_BaseClassfications(self):
        obj = self.factory_cls.build(content_object=ContentType.objects.first())

        with pytest.raises(ValidationError):
            obj.clean_fields()

    def test_object_id_can_not_be_null(self):
        assert not self.model._meta.get_field("object_id").null

    def test_is_seed_defaults_to_False(self):
        assert not self.model._meta.get_field("is_seed").default

    # properties
    @pytest.mark.parametrize("is_seed", [True, False])
    def test_to_tree_node_return_TaxonProbNode_sets_is_seed(self, taxon_specie, is_seed):
        with patch(
            f"{TaxonClassificationCandidate.__module__}.{TaxonClassificationCandidate.__name__}.clean",
            return_value=None,
        ):
            obj = self.factory_cls(label=taxon_specie, probability=0.666, is_seed=is_seed)

        assert obj.to_tree_node.is_seed == obj.is_seed

    # object manager
    def test_objects_get_consensus(self, taxon_root):
        # Creating a simple taxonomy tree
        taxon_class1 = TaxonFactory(name="class1", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
        taxon_specie1_1 = TaxonFactory(name="specie1_1", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class1)
        taxon_specie1_2 = TaxonFactory(name="specie1_2", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class1)

        _ = TaxonClassificationCandidateFactory(taxon=taxon_root, probability=1)
        tc_class1 = TaxonClassificationCandidateFactory(taxon=taxon_class1, probability=1)
        tc_specie1_1 = TaxonClassificationCandidateFactory(taxon=taxon_specie1_1, probability=0.75)
        _ = TaxonClassificationCandidateFactory(taxon=taxon_specie1_2, probability=0.25)

        assert TaxonClassificationCandidate.objects.get_consensus(min_prob=0.1, min_taxon_rank=None) == tc_specie1_1
        assert TaxonClassificationCandidate.objects.get_consensus(min_prob=0.75, min_taxon_rank=None) == tc_specie1_1
        assert TaxonClassificationCandidate.objects.get_consensus(min_prob=0.8, min_taxon_rank=None) == tc_class1
        assert (
            TaxonClassificationCandidate.objects.get_consensus(min_prob=0.8, min_taxon_rank=Taxon.TaxonomicRank.CLASS)
            == tc_class1
        )

        with pytest.raises(TaxonClassificationCandidate.DoesNotExist):
            TaxonClassificationCandidate.objects.get_consensus(min_prob=10)

    # methods
    @pytest.mark.parametrize(
        "model, is_seed, create, expected_raise",
        [
            (BasePhotoIdentification, True, True, does_not_raise()),
            (BasePhotoIdentification, True, False, does_not_raise()),
            (BasePhotoIdentification, False, True, does_not_raise()),
            (BasePhotoIdentification, False, False, does_not_raise()),
            (BaseClassification, True, True, pytest.raises(ValidationError)),
            (BaseClassification, True, False, does_not_raise()),
            (BaseClassification, False, True, does_not_raise()),
            (BaseClassification, False, False, does_not_raise()),
        ],
    )
    def test_clean_raise_ValidationError_if_is_seed_and_not_subclass_BasePhotoIdentification(
        self, model, is_seed, create, expected_raise
    ):
        if create:
            obj = self.factory_cls.create(is_seed=is_seed)
        else:
            obj = self.factory_cls.build(is_seed=is_seed)

        # Case object is not created
        with patch.object(obj.content_type, "model_class", return_value=model):
            with expected_raise:
                obj.clean()

    def test_save_call_full_clean_with_exclude(self):
        obj = self.factory_cls()

        with patch.object(obj, "full_clean", return_value=None) as mock_method:
            obj.save()

            mock_method.assert_called_once()
            assert "content_type" not in mock_method.call_args.kwargs["exclude"]

    # meta
    def test_constraint_unique_classification_candidate_by_label(self, taxon_specie):
        obj_classification = DummyClassificationFactory()
        with pytest.raises(IntegrityError, match=r"unique constraint"):
            self.factory_cls.create_batch(size=2, content_object=obj_classification, label=taxon_specie)


class BaseTestBaseClassification(BaseTestObservableMixin, ABC):
    def test__notify_changes_is_called_on_sex_change(self):
        super().assert__notify_changes_is_called_on_field_change(
            fieldname="sex",
        )

    def test__notify_changes_is_called_on_candidates_change(self):
        super().assert__notify_changes_is_called_on_field_change(
            fieldname="candidates",
        )

    # fields
    def test_candidates_related_query_name(self):
        assert self.model._meta.get_field("candidates").remote_field.related_name == "result"

    def test_sex_can_be_null(self):
        assert self.model._meta.get_field("sex").null

    def test_sex_can_be_blank(self):
        assert self.model._meta.get_field("sex").blank

    def test_sex_choices_are_male_and_female(self):
        assert frozenset(self.model._meta.get_field("sex").choices) == frozenset([("M", "Male"), ("F", "Female")])

    # method
    def test__notify_changes_send_classification_has_changed_signal_only_if_fields_in_NOTIFY_ON_FIELD_CHANGE(self):
        obj = self.factory_cls()

        fake_fields = ["fake_field1", "fake_field2"]
        fields_changed = fake_fields + self.model.NOTIFY_ON_FIELD_CHANGE

        with patch.object(classification_has_changed, "send", return_value=None) as mocked_signal:
            obj._notify_changes(fields_changed=fields_changed)

            mocked_signal.assert_called_once_with(
                sender=obj.__class__, instance=obj, fields_changed=self.model.NOTIFY_ON_FIELD_CHANGE
            )

    @patch(
        f"{TaxonClassificationCandidate.__module__}.{TaxonClassificationCandidate.__name__}.clean",
        return_value=None,
    )
    def test_get_classification_tree_with_candidates(self, patcher, taxon_root):
        # Creating a simple taxonomy tree
        taxon_class1 = TaxonFactory(name="class1", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
        taxon_specie1_1 = TaxonFactory(name="specie1_1", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class1)
        taxon_specie1_2 = TaxonFactory(name="specie1_2", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class1)
        taxon_class2 = TaxonFactory(name="class2", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
        # Needed to know that does not expand.
        _ = TaxonFactory(name="specie2_1", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class2)

        obj = self.factory_cls()
        # Defining candidates:
        TaxonClassificationCandidateFactory(label=taxon_root, probability=Decimal("1"), content_object=obj),
        TaxonClassificationCandidateFactory(label=taxon_class1, probability=Decimal("0.8"), content_object=obj),
        TaxonClassificationCandidateFactory(
            label=taxon_specie1_1, probability=Decimal("0.7"), is_seed=True, content_object=obj
        ),
        TaxonClassificationCandidateFactory(label=taxon_specie1_2, probability=Decimal("0.1"), content_object=obj),
        TaxonClassificationCandidateFactory(label=taxon_class2, probability=Decimal("0.1"), content_object=obj),

        expected_prob_tree = TaxonProbNode(
            taxon=taxon_root,
            probability=Decimal("1"),
            children=[
                TaxonProbNode(
                    taxon=taxon_class1,
                    probability=Decimal("0.8"),
                    children=[
                        TaxonProbNode(taxon=taxon_specie1_1, probability=0.7, is_seed=True),
                        TaxonProbNode(taxon=taxon_specie1_2, probability=0.1),
                    ],
                ),
                TaxonProbNode(taxon=taxon_class2, probability=0.1),
            ],
        )

        assert obj.get_classification_tree().to_dict == expected_prob_tree.to_dict

    def test_get_classification_tree_without_candidates(self, taxon_root):
        obj = self.factory_cls(candidates=[])

        expected_prob_tree = TaxonProbNode(taxon=taxon_root, probability=1)
        assert obj.get_classification_tree().to_dict == expected_prob_tree.to_dict

    @patch(
        f"{TaxonClassificationCandidate.__module__}.{TaxonClassificationCandidate.__name__}.clean",
        return_value=None,
    )
    def test_recompute_candidates_tree_with_seeds_use_them_only_for_create_tree(self, patcher, taxon_root):
        # Creating a simple taxonomy tree
        taxon_class1 = TaxonFactory(name="class1", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
        taxon_specie1_1 = TaxonFactory(name="specie1_1", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class1)
        taxon_specie1_2 = TaxonFactory(name="specie1_2", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class1)
        taxon_class2 = TaxonFactory(name="class2", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
        # Needed to know that does not expand.
        _ = TaxonFactory(name="specie2_1", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class2)

        obj = self.factory_cls()

        TaxonClassificationCandidateFactory(label=taxon_root, probability=Decimal("1"), content_object=obj),
        TaxonClassificationCandidateFactory(label=taxon_class1, probability=Decimal("0.8"), content_object=obj),
        TaxonClassificationCandidateFactory(
            label=taxon_specie1_1, probability=Decimal("0.7"), is_seed=True, content_object=obj
        ),
        TaxonClassificationCandidateFactory(label=taxon_specie1_2, probability=Decimal("0.1"), content_object=obj),
        TaxonClassificationCandidateFactory(label=taxon_class2, probability=Decimal("0.2"), content_object=obj),

        expected_prob_tree = TaxonProbNode(
            taxon=taxon_root,
            probability=Decimal("1"),
            children=[
                TaxonProbNode(
                    taxon=taxon_class1,
                    probability=Decimal("1"),
                    children=[
                        TaxonProbNode(taxon=taxon_specie1_1, probability=0.7, is_seed=True),
                        TaxonProbNode(taxon=taxon_specie1_2, probability=0.3),
                    ],
                ),
            ],
        )

        has_changed = obj.recompute_candidates_tree()

        assert has_changed is True

        assert obj.get_classification_tree().to_dict == expected_prob_tree.to_dict

    def test_recompute_canidates_tree_without_seeds(self, taxon_root):
        # Creating a simple taxonomy tree
        taxon_class1 = TaxonFactory(name="class1", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
        taxon_specie1_1 = TaxonFactory(name="specie1_1", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class1)
        taxon_specie1_2 = TaxonFactory(name="specie1_2", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class1)
        taxon_class2 = TaxonFactory(name="class2", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
        # Needed to know that does not expand.
        taxon_specie2_1 = TaxonFactory(name="specie2_1", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class2)

        obj = self.factory_cls()

        TaxonClassificationCandidateFactory(label=taxon_root, probability=Decimal("1"), content_object=obj),
        TaxonClassificationCandidateFactory(label=taxon_class1, probability=Decimal("0.8"), content_object=obj),
        TaxonClassificationCandidateFactory(label=taxon_specie1_1, probability=Decimal("0.7"), content_object=obj),
        TaxonClassificationCandidateFactory(label=taxon_specie1_2, probability=Decimal("0.1"), content_object=obj),
        TaxonClassificationCandidateFactory(label=taxon_class2, probability=Decimal("0.2"), content_object=obj),

        expected_prob_tree = TaxonProbNode(
            taxon=taxon_root,
            probability=Decimal("1"),
            children=[
                TaxonProbNode(
                    taxon=taxon_class1,
                    probability=Decimal("0.8"),
                    children=[
                        TaxonProbNode(taxon=taxon_specie1_1, probability=0.7),
                        TaxonProbNode(taxon=taxon_specie1_2, probability=0.1),
                    ],
                ),
                TaxonProbNode(
                    taxon=taxon_class2,
                    probability=0.2,
                    children=[TaxonProbNode(taxon=taxon_specie2_1, probability=0.2)],
                ),
            ],
        )

        has_changed = obj.recompute_candidates_tree()

        assert has_changed is True

        assert obj.get_classification_tree().to_dict == expected_prob_tree.to_dict

    def test_update_candidates_from_tree_rollback_if_error(self, freezer, taxon_root, taxon_specie):
        yesterday = timezone.now() - timedelta(days=1)
        freezer.move_to(yesterday)

        obj = self.factory_cls()
        TaxonClassificationCandidateFactory(label=taxon_specie, probability=1, content_object=obj)

        original_candidates = frozenset(obj.candidates.all())

        now = timezone.now()
        freezer.move_to(now)
        with patch(
            f"{TaxonClassificationCandidate.__module__}.TaxonClassificationCandidate.objects.get",
            side_effect=DatabaseError(),
        ):
            with pytest.raises(DatabaseError):
                obj.update_candidates_from_tree(tree=TaxonProbNodeFactory(taxon=taxon_root))

        assert frozenset(obj.candidates.all()) == original_candidates
        assert obj.updated_at == yesterday
        for c in obj.candidates.all():
            assert c.updated_at == yesterday

    def test_update_candidates_from_tree_delete_all_if_tree_is_empty(self, freezer, taxon_specie):
        yesterday = timezone.now() - timedelta(days=1)
        freezer.move_to(yesterday)

        obj = self.factory_cls()
        TaxonClassificationCandidateFactory(label=taxon_specie, probability=1, content_object=obj)

        now = timezone.now()
        freezer.move_to(now)

        with patch.object(obj, "_notify_changes", return_value=None) as mocked_notify_changes:
            result = obj.update_candidates_from_tree(tree=None)

            mocked_notify_changes.assert_called_once_with(fields_changed=["candidates"])

        assert not obj.candidates.exists()
        assert obj.updated_at == now
        assert result is True

    @patch(
        f"{TaxonClassificationCandidate.__module__}.{TaxonClassificationCandidate.__name__}.clean",
        return_value=None,
    )
    def test_update_candidates_from_tree_only_update(self, patched, freezer, taxon_specie):
        yesterday = timezone.now() - timedelta(days=1)
        freezer.move_to(yesterday)

        obj = self.factory_cls()

        TaxonClassificationCandidateFactory(label=taxon_specie, probability=1, is_seed=False, content_object=obj)

        assert obj.candidates.count() == 1

        now = timezone.now()
        freezer.move_to(now)

        with patch.object(obj, "_notify_changes", return_value=None) as mocked_notify_changes:
            has_changed = obj.update_candidates_from_tree(
                tree=TaxonProbNodeFactory(taxon=taxon_specie, probability=0.5, is_seed=True)
            )

            mocked_notify_changes.assert_called_once_with(fields_changed=["candidates"])

        assert has_changed is True
        assert obj.candidates.count() == 1
        assert obj.candidates.first().label == taxon_specie
        assert obj.candidates.first().probability == 0.5
        assert obj.candidates.first().is_seed is True
        assert obj.candidates.first().updated_at == now

    @patch(
        f"{TaxonClassificationCandidate.__module__}.{TaxonClassificationCandidate.__name__}.clean",
        return_value=None,
    )
    def test_update_candidates_from_tree_without_update_changes(self, patcher, freezer, taxon_specie):
        yesterday = timezone.now() - timedelta(days=1)
        freezer.move_to(yesterday)

        obj = self.factory_cls()

        TaxonClassificationCandidateFactory(label=taxon_specie, probability=1, is_seed=True, content_object=obj)

        assert obj.candidates.count() == 1

        now = timezone.now()
        freezer.move_to(now)

        with patch.object(obj, "_notify_changes", return_value=None) as mocked_notify_changes:
            has_changed = obj.update_candidates_from_tree(
                tree=TaxonProbNodeFactory(taxon=taxon_specie, probability=1, is_seed=True)
            )

            mocked_notify_changes.assert_not_called()

        assert obj.candidates.count() == 1
        assert obj.candidates.first().label == taxon_specie
        assert obj.candidates.first().probability == 1
        assert obj.candidates.first().is_seed is True
        assert obj.candidates.first().updated_at == yesterday
        assert obj.updated_at == yesterday
        assert has_changed is False

    @patch(
        f"{TaxonClassificationCandidate.__module__}.{TaxonClassificationCandidate.__name__}.clean",
        return_value=None,
    )
    def test_update_candidates_from_tree_with_creations(self, patcher, freezer, taxon_root, taxon_specie):
        yesterday = timezone.now() - timedelta(days=1)
        freezer.move_to(yesterday)

        obj = self.factory_cls()

        TaxonClassificationCandidateFactory(label=taxon_root, probability=1, is_seed=False, content_object=obj)

        assert obj.candidates.count() == 1

        now = timezone.now()
        freezer.move_to(now)

        with patch.object(obj, "_notify_changes", return_value=None) as mocked_notify_changes:
            has_changed = obj.update_candidates_from_tree(
                tree=TaxonProbNodeFactory(
                    taxon=taxon_root,
                    probability=1,
                    children=[TaxonProbNodeFactory(taxon=taxon_specie, probability=1, is_seed=True)],
                )
            )

            mocked_notify_changes.assert_called_once_with(fields_changed=["candidates"])

        assert obj.candidates.count() == 2
        assert obj.candidates.first().label == taxon_root
        assert obj.candidates.first().probability == 1
        assert obj.candidates.first().is_seed is False
        assert obj.candidates.first().updated_at == yesterday
        assert obj.candidates.last().label == taxon_specie
        assert obj.candidates.last().probability == 1
        assert obj.candidates.last().is_seed is True
        assert obj.candidates.last().created_at == now
        assert obj.candidates.last().updated_at == now
        assert has_changed is True


class BaseTestBaseIdentification(BaseTestBaseShape, BaseTestBaseClassification):
    @pytest.mark.parametrize("fieldname", ["points", "shape_type"])
    def test__notify_changes_is_called_on_shape_change(self, fieldname):
        super().assert__notify_changes_is_called_on_field_change(
            fieldname=fieldname,
        )


##########################
# Task definition
##########################


class BaseTestBaseTaskWithResults(BaseTestBaseTask, ABC):
    @property
    @abstractmethod
    def task_result_model(self):
        return NotImplementedError

    @abstractmethod
    def test__run_on_result_change(self):
        raise NotImplementedError

    def test__results_related_name_is_results(self):
        self.model._results_related_name == "results"

    def test_update_results_calls_recompute_results_for_each_result_type(self):
        obj = self.factory_cls()

        with patch(
            f"{self.task_result_model.__module__}.{self.task_result_model.__name__}.recompute_result",
            return_value=True,
        ) as mocked_recompute_results:
            obj.update_results()

        assert mocked_recompute_results.call_count == len(self.task_result_model.ResultType)
        assert mocked_recompute_results.call_args == call(from_candidates=False)

    def test_update_results_call__run_on_result_chang_only_once(self):
        obj = self.factory_cls()

        mocked_run_on_result_change = Mock(return_value=None)
        obj._run_on_result_change = mocked_run_on_result_change

        with patch(
            f"{self.task_result_model.__module__}.{self.task_result_model.__name__}.has_changed",
            return_value=True,
        ):
            with patch(
                f"{self.task_result_model.__module__}.{self.task_result_model.__name__}._recompute_label_consensus",
                return_value=True,
            ):
                obj.update_results()

        mocked_run_on_result_change.assert_called_once()

    def test___run_on_is_completed_changes_sends_signal(self):
        obj = self.factory_cls()

        with patch.object(identification_task_has_changed, "send", return_value=None) as mocked_signal:
            obj._run_on_is_completed_changes()

            mocked_signal.assert_called_once_with(sender=self.model, instance=obj, fields_changed=["is_completed"])


class BaseTestBaseTaskChild(BaseTestObservableMixin, BaseTestTimeStampedModel, ABC):
    @property
    @abstractmethod
    def task_model(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def task_factory_cls(self):
        raise NotImplementedError

    # fields
    def test_task_fk_model(self):
        assert self.model.task.field.related_model is self.task_model

    def test_task_can_not_be_null(self):
        assert not self.model._meta.get_field("task").null

    def test_task_is_not_editable(self):
        assert not self.model._meta.get_field("task").editable

    def test_task_field_cascade_on_delete(self):
        _on_delete = self.model._meta.get_field("task").remote_field.on_delete
        assert _on_delete == models.CASCADE

    # methods
    def test_skip_notify_changes_parent_is_default_False(self):
        assert not self.factory_cls.build().skip_notify_changes_parent

    def test__run_on_notify_changes_to_parent(self):
        obj = self.factory_cls()

        with patch.object(obj.task, "save") as mocked_task_save:
            obj._run_on_notify_changes_to_parent()
            mocked_task_save.assert_called_once_with(update_fields=["updated_at", "is_completed"])

    def test_run_on_notify_changes_to_parent_changes_updated_at_in_task(self, freezer):
        creation_date = timezone.now() - timedelta(days=10)
        freezer.move_to(creation_date)

        obj = self.factory_cls()

        next_day = timezone.now() + timedelta(days=1)
        freezer.move_to(next_day)

        obj._run_on_notify_changes_to_parent()

        assert obj.created_at == creation_date
        assert obj.updated_at == creation_date
        assert obj.task.created_at == creation_date
        assert obj.task.updated_at == next_day

    @pytest.mark.parametrize("skip_notify_changes_parent", [True, False])
    def test_notify_changes_to_parent_calls__run_on_notify_changes_to_parent(self, skip_notify_changes_parent):
        obj = self.factory_cls.build(skip_notify_changes_parent=skip_notify_changes_parent)

        with patch.object(obj, "_run_on_notify_changes_to_parent") as mocked_method:
            obj.notify_changes_to_parent()

            if skip_notify_changes_parent:
                mocked_method.assert_not_called()
            else:
                mocked_method.assert_called_once()

    def test__notify_changes_calls__notify_changes_to_parent(self):
        obj = self.factory_cls()

        with patch.object(obj, "notify_changes_to_parent", return_value=None) as mocked_method:
            obj._notify_changes()

            mocked_method.assert_called_once()

    def test_on_create_changes_task_updated_at_to_now(self, freezer):
        creation_date = timezone.now() - timedelta(days=10)
        freezer.move_to(creation_date)

        task = self.task_factory_cls()

        next_day = timezone.now() + timedelta(days=1)
        freezer.move_to(next_day)

        obj = self.factory_cls(task=task)

        assert obj.created_at == next_day
        assert obj.updated_at == next_day
        assert obj.task.created_at == creation_date
        assert obj.task.updated_at == next_day

    def test_delete_changes_task_updated_at_to_now(self, freezer):
        creation_date = timezone.now() - timedelta(days=10)
        freezer.move_to(creation_date)

        obj = self.factory_cls()

        next_day = timezone.now() + timedelta(days=1)
        freezer.move_to(next_day)

        obj.delete()

        assert obj.task.created_at == creation_date
        assert obj.task.updated_at == next_day


@pytest.mark.django_db
class TestIndividualIdentificationTask(BaseTestBaseTaskWithResults):
    model = IndividualIdentificationTask
    factory_cls = IndividualIdentificationTaskFactory

    task_result_model = IndividualIdentificationTaskResult

    def test_is_created_on_individual_creation(self):
        ind = IndividualFactory.create(mute_signals=False, identification_task=None)
        assert ind.identification_task.pk

    # fields
    def test_individual_can_not_be_null(self):
        assert not self.model._meta.get_field("individual").null

    def test_individual_is_primary_key(self):
        assert self.model._meta.get_field("individual").primary_key

    def test_individual_is_not_editable(self):
        assert not self.model._meta.get_field("individual").editable

    def test_pk_is_get_from_individual(self):
        i = IndividualFactory(identification_task=None)
        obj = self.factory_cls(individual=i)

        assert obj.pk == i.pk

    def test_individual_related_name(self):
        assert self.model._meta.get_field("individual").remote_field.related_name == "identification_task"

    def test_individual_on_delete_cascade(self):
        _on_delete = self.model._meta.get_field("individual").remote_field.on_delete
        assert _on_delete == models.CASCADE

    def test_is_locked_can_not_be_null(self):
        assert not self.model._meta.get_field("is_locked").null

    def test_is_locked_default_is_False(self):
        assert self.factory_cls().is_locked is False

    # methods
    def test__run_on_result_change(self):
        # Test do nothing + not raise
        self.factory_cls.build()._run_on_result_change()

    def test__get_is_completed_value(self):
        # Returns True if any photo identification is completed.
        obj = self.factory_cls()

        assert not obj._get_is_completed_value()

        _ = PhotoIdentificationTaskFactory(task=obj, is_completed=False)

        assert not obj._get_is_completed_value()

        _ = PhotoIdentificationTaskFactory(task=obj, is_completed=True)

        assert obj._get_is_completed_value()


@pytest.mark.django_db
class TestPhotoIdentificationTask(BaseTestBaseTaskWithResults, BaseTestBaseTaskChild, BaseTestBasePhotoAnnotationTask):
    model = PhotoIdentificationTask
    factory_cls = PhotoIdentificationTaskFactory

    task_result_model = PhotoIdentificationTaskResult

    task_model = IndividualIdentificationTask
    task_factory_cls = IndividualIdentificationTaskFactory

    def test__notify_changes_is_called_on_is_completed_change(self):
        super().assert__notify_changes_is_called_on_field_change(fieldname="is_completed")

    # fields
    def test_task_can_not_be_null(self):
        assert not self.model._meta.get_field("task").null

    def test_task_on_delete_cascade(self):
        _on_delete = self.model._meta.get_field("task").remote_field.on_delete
        assert _on_delete == models.CASCADE

    def test_task_related_name(self):
        assert self.model._meta.get_field("task").remote_field.related_name == "photo_identification_tasks"

    def test_total_external_field_can_not_be_None(self):
        self.test_counter_field_can_not_be_None(field_name="total_external")

    def test_total_external_field_can_not_be_negative(self):
        self.test_counter_field_can_not_be_negative(field_name="total_external")

    def test_total_external_field_defaults_to_0(self):
        self.test_counter_field_defaults_to_0(field_name="total_external")

    def test_total_external_field_can_not_be_editable(self):
        self.test_counter_field_can_not_be_editable(field_name="total_external")

    def test_total_external_fields_are_indexed(self):
        self.test_counter_fields_are_indexed(field_name="total_external")

    # properties
    def test_individual_returns_parent_task_individual(self):
        obj = self.factory_cls()

        assert obj.individual == obj.task.individual

    @pytest.mark.parametrize("value", [True, False])
    def test_is_locked_returns_from_parent_task(self, value):
        obj = self.factory_cls(task__is_locked=value)

        assert obj.is_locked == value

    # methods
    def test___get_is_completed_value_keeps_True_if_completed_and_has_total_annotations(self):
        obj = self.factory_cls()
        obj.total_annotations = 1
        obj.is_completed = True

        assert obj._get_is_completed_value()

    @pytest.mark.parametrize(
        "total_annotations, expected_result",
        [
            (NUM_USER_IDENTIFICATIONS_TO_COMPLETE - 1, False),
            (NUM_USER_IDENTIFICATIONS_TO_COMPLETE, True),
            (NUM_USER_IDENTIFICATIONS_TO_COMPLETE + 1, True),
        ],
    )
    def test__get_is_completed_value_True_if_total_annotations_gte_NUM_USER_IDENTIFICAITONS(
        self, total_annotations, expected_result
    ):
        obj = self.factory_cls()
        obj.total_annotations = total_annotations
        obj.is_completed = False

        assert obj._get_is_completed_value() == expected_result

    def test__get_is_completed_value_if_photo_task_result_contains_ground_truth(self):
        obj = self.factory_cls()
        _ = PhotoIdentificationTaskResultFactory(
            task=obj, is_ground_truth=True, type=BaseTaskResult.ResultType.COMMUNITY
        )

        obj.total_annotations = 0
        obj.is_completed = False

        assert obj._get_is_completed_value()

    def test__run_on_result_change(self):
        # Test calls task.update_results()
        obj = self.factory_cls.build()

        with patch.object(obj.task, "update_results") as mocked_method:
            obj._run_on_result_change()

            mocked_method.assert_called_once()

    @pytest.mark.django_db(transaction=True)
    def test_increase_external_counter_func_in_rase_condition(self):
        self.test_increase_counter_func_in_race_condition(
            func_name="increase_external_counter", field_name="total_external"
        )

    @pytest.mark.django_db(transaction=True)
    def test_decrease_external_counter_func_in_rase_condition(self):
        self.test_decrease_counter_func_in_race_condition(
            func_name="decrease_external_counter", field_name="total_external"
        )

    # meta
    def test_constraint_unique_by_task_and_photo(self):
        photo = PhotoFactory()
        ind_task = IndividualIdentificationTaskFactory()
        with pytest.raises(IntegrityError, match=r"unique constraint"):
            self.factory_cls.create_batch(size=2, task=ind_task, photo=photo)


##########################
# Identification definition
##########################


class BaseTestBasePhotoIdentification(BaseTestBaseTaskChild, BaseTestBaseIdentification, ABC):
    task_model = PhotoIdentificationTask
    task_factory_cls = PhotoIdentificationTaskFactory

    # fields

    # objects manager
    def test_object_manager_finished(self):
        objs = self.factory_cls.create_batch(size=5)

        assert frozenset(self.model.objects.finished().all()) == frozenset(objs)

    def test_create_raises_if_task_is_locked(self):
        task = PhotoIdentificationTaskFactory(task__is_locked=True)

        with pytest.raises(ValueError):
            _ = self.factory_cls(task=task)

    def test_save_raises_if_task_is_locked(self):
        # Start with non locked task
        task = PhotoIdentificationTaskFactory(task__is_locked=False)

        # Should not raise
        obj = self.factory_cls(task=task)

        # Lock parent task
        task.task.is_locked = True
        task.task.save()

        with pytest.raises(ValueError):
            obj.save()

    # methods
    def test__run_on_notify_changes_to_parent_call_task_update_results(self):
        obj = self.factory_cls()

        with patch.object(obj.task, "update_results", return_value=None) as mocked_method:
            obj._run_on_notify_changes_to_parent()

            mocked_method.assert_called_once()


@pytest.mark.django_db
class TestUserIdentification(BaseTestBasePhotoIdentification):
    model = UserIdentification
    factory_cls = UserIdentificationFactory

    def test__notify_changes_is_called_on_is_ground_truth_change(self):
        super().assert__notify_changes_is_called_on_field_change(
            fieldname="is_ground_truth",
        )

    def test__notify_changes_is_called_on_was_skipped_change(self):
        super().assert__notify_changes_is_called_on_field_change(
            fieldname="was_skipped",
        )

    # fields
    def test_user_can_be_null(self):
        assert self.model._meta.get_field("user").null

    def test_user_is_set_null_on_delete(self):
        _on_delete = self.model._meta.get_field("user").remote_field.on_delete
        assert _on_delete == models.SET_NULL

    def test_user_related_name(self):
        assert self.model._meta.get_field("user").remote_field.related_name == "identifications"

    def test_lead_time_can_be_null(self):
        assert self.model._meta.get_field("lead_time").null

    def test_lead_time_default_is_None(self):
        assert self.model._meta.get_field("lead_time").default is None

    def test_lead_time_is_not_editable(self):
        assert not self.model._meta.get_field("lead_time").editable

    def test_is_ground_truth_can_not_be_null(self):
        assert not self.model._meta.get_field("is_ground_truth").null

    def test_is_ground_truth_default_is_False(self):
        assert self.model._meta.get_field("is_ground_truth").default is False

    def test_was_skipped_can_not_be_null(self):
        assert not self.model._meta.get_field("was_skipped").null

    def test_was_skipped_default_is_False(self):
        assert self.model._meta.get_field("was_skipped").default is False

    # object manager
    def test_object_manager_finished_filters_out_skipped_objects(self):
        objs = self.factory_cls.create_batch(size=5)

        skipped_objects = self.factory_cls.create_batch(size=5, was_skipped=True)

        assert frozenset(self.model.objects.all()) == frozenset(objs + skipped_objects)

        assert frozenset(self.model.objects.finished()) == frozenset(objs)

    # methods
    @pytest.mark.parametrize("was_skipped", [True, False])
    def test_on_create_counters(self, was_skipped):
        photo_task = PhotoIdentificationTaskFactory()

        assert photo_task.skipped_annotations == 0
        assert photo_task.total_annotations == 0
        assert photo_task.total_predictions == 0
        assert photo_task.total_external == 0

        _ = self.factory_cls(task=photo_task, was_skipped=was_skipped)

        assert photo_task.total_predictions == 0
        assert photo_task.total_external == 0

        if was_skipped:
            assert photo_task.skipped_annotations == 1
            assert photo_task.total_annotations == 0
        else:
            assert photo_task.skipped_annotations == 0
            assert photo_task.total_annotations == 1

    def test_on_simple_save_does_not_update_counters(self):
        photo_task = PhotoIdentificationTaskFactory()

        assert photo_task.skipped_annotations == 0
        assert photo_task.total_annotations == 0
        assert photo_task.total_predictions == 0
        assert photo_task.total_external == 0

        obj = self.factory_cls(task=photo_task)

        assert photo_task.skipped_annotations == 0
        assert photo_task.total_annotations == 1
        assert photo_task.total_predictions == 0
        assert photo_task.total_external == 0

        obj.save()

        assert photo_task.skipped_annotations == 0
        assert photo_task.total_annotations == 1
        assert photo_task.total_predictions == 0
        assert photo_task.total_external == 0

    @pytest.mark.parametrize("was_skipped", [True, False])
    def test_on_was_skipped_change_counters_are_updated(self, was_skipped):
        photo_task = PhotoIdentificationTaskFactory()

        assert photo_task.skipped_annotations == 0
        assert photo_task.total_annotations == 0
        assert photo_task.total_predictions == 0
        assert photo_task.total_external == 0

        obj = self.factory_cls(task=photo_task, was_skipped=was_skipped)
        obj.was_skipped = not was_skipped
        obj.save()

        assert photo_task.total_predictions == 0
        assert photo_task.total_external == 0

        if obj.was_skipped:
            assert photo_task.skipped_annotations == 1
            assert photo_task.total_annotations == 0
        else:
            assert photo_task.skipped_annotations == 0
            assert photo_task.total_annotations == 1

    @pytest.mark.parametrize("was_skipped", [True, False])
    def test_on_delete_counters_are_updated(self, was_skipped):
        photo_task = PhotoIdentificationTaskFactory()

        assert photo_task.skipped_annotations == 0
        assert photo_task.total_annotations == 0
        assert photo_task.total_predictions == 0
        assert photo_task.total_external == 0

        obj = self.factory_cls(task=photo_task, was_skipped=was_skipped)
        obj.delete()

        assert photo_task.skipped_annotations == 0
        assert photo_task.total_annotations == 0
        assert photo_task.total_predictions == 0
        assert photo_task.total_external == 0

    # Meta
    def test_constraint_unique_user_by_task(self):
        task = PhotoIdentificationTaskFactory()
        user = UserFactory()
        with pytest.raises(IntegrityError, match=r"unique constraint"):
            self.factory_cls.create_batch(size=2, user=user, task=task)

    def test_constraint_unique_ground_truth_by_task(self):
        task = PhotoIdentificationTaskFactory()

        # Does not raise if ground truth is false
        self.factory_cls.create_batch(size=2, is_ground_truth=False, task=task)

        # Create one ground truth
        self.factory_cls(is_ground_truth=True, task=task)

        with pytest.raises(IntegrityError, match=r"unique constraint"):
            self.factory_cls(is_ground_truth=True, task=task)

    def test_constraint_skipped_identification_can_not_be_ground_truth(self):
        with pytest.raises(IntegrityError, match=r"check constraint"):
            _ = self.factory_cls(was_skipped=True, is_ground_truth=True)


@pytest.mark.django_db
class TestPrediction(BaseTestBasePhotoIdentification):
    model = Prediction
    factory_cls = PredictionFactory

    # methods
    def test_on_create_increase_prediction_counter(self):
        photo_task = PhotoIdentificationTaskFactory()

        assert photo_task.total_predictions == 0
        assert photo_task.total_annotations == 0
        assert photo_task.skipped_annotations == 0
        assert photo_task.total_external == 0

        _ = self.factory_cls(task=photo_task)

        assert photo_task.total_predictions == 1
        assert photo_task.total_annotations == 0
        assert photo_task.skipped_annotations == 0
        assert photo_task.total_external == 0

    def test_on_simple_save_does_not_update_counters(self):
        photo_task = PhotoIdentificationTaskFactory()

        assert photo_task.skipped_annotations == 0
        assert photo_task.total_annotations == 0
        assert photo_task.total_predictions == 0
        assert photo_task.total_external == 0

        obj = self.factory_cls(task=photo_task)

        assert photo_task.skipped_annotations == 0
        assert photo_task.total_annotations == 0
        assert photo_task.total_predictions == 1
        assert photo_task.total_external == 0

        obj.save()

        assert photo_task.skipped_annotations == 0
        assert photo_task.total_annotations == 0
        assert photo_task.total_predictions == 1
        assert photo_task.total_external == 0

    def test_on_delete_decrease_prediction_counter(self):
        photo_task = PhotoIdentificationTaskFactory()

        assert photo_task.skipped_annotations == 0
        assert photo_task.total_annotations == 0
        assert photo_task.total_predictions == 0
        assert photo_task.total_external == 0

        obj = self.factory_cls(task=photo_task)

        assert photo_task.total_predictions == 1

        obj.delete()

        assert photo_task.skipped_annotations == 0
        assert photo_task.total_annotations == 0
        assert photo_task.total_predictions == 0
        assert photo_task.total_external == 0


@pytest.mark.django_db
class TestExternalIdentification(BaseTestBasePhotoIdentification):
    model = ExternalIdentification
    factory_cls = ExternalIdentificationFactory

    # methods
    def test_on_create_increase_external_counter(self):
        photo_task = PhotoIdentificationTaskFactory()

        assert photo_task.total_predictions == 0
        assert photo_task.total_annotations == 0
        assert photo_task.skipped_annotations == 0
        assert photo_task.total_external == 0

        _ = self.factory_cls(task=photo_task)

        assert photo_task.total_predictions == 0
        assert photo_task.total_annotations == 0
        assert photo_task.skipped_annotations == 0
        assert photo_task.total_external == 1

    def test_on_simple_save_does_not_update_counters(self):
        photo_task = PhotoIdentificationTaskFactory()

        assert photo_task.skipped_annotations == 0
        assert photo_task.total_annotations == 0
        assert photo_task.total_predictions == 0
        assert photo_task.total_external == 0

        obj = self.factory_cls(task=photo_task)

        assert photo_task.skipped_annotations == 0
        assert photo_task.total_annotations == 0
        assert photo_task.total_predictions == 0
        assert photo_task.total_external == 1

        obj.save()

        assert photo_task.skipped_annotations == 0
        assert photo_task.total_annotations == 0
        assert photo_task.total_predictions == 0
        assert photo_task.total_external == 1

    def test_on_delete_decrease_external_counter(self):
        photo_task = PhotoIdentificationTaskFactory()

        assert photo_task.skipped_annotations == 0
        assert photo_task.total_annotations == 0
        assert photo_task.total_predictions == 0
        assert photo_task.total_external == 0

        obj = self.factory_cls(task=photo_task)

        assert photo_task.total_external == 1

        obj.delete()

        assert photo_task.skipped_annotations == 0
        assert photo_task.total_annotations == 0
        assert photo_task.total_predictions == 0
        assert photo_task.total_external == 0


##########################
# Task Results
##########################


class BaseTestBaseTaskResult(BaseTestBaseTaskChild, ABC):
    # fields
    def test_task_related_name(self):
        assert self.model._meta.get_field("task").remote_field.related_name == "results"

    # methods
    @abstractmethod
    def test_recompute_result(self):
        raise NotImplementedError

    def test__run_on_notify_changes_to_parent_call_task__run_on_result_change(self):
        obj = self.factory_cls()

        with patch.object(obj.task, "_run_on_result_change") as mocked_method:
            obj._run_on_notify_changes_to_parent()

            mocked_method.assert_called_once()

    # meta
    def test_constraint_unique_type_by_task(self):
        task = self.task_factory_cls()

        with pytest.raises(IntegrityError, match=r"unique constraint"):
            _ = self.factory_cls.create_batch(size=2, task=task, type=list(BaseTaskResult.ResultType)[0])


class BaseTestBaseClassificationTaskResult(
    BaseTestBaseTaskResult, BaseTestBaseClassification, BaseTestBaseTaxonAnnotation, ABC
):
    # properties
    @abstractmethod
    def test_related_classifications(self):
        raise NotImplementedError

    # methods
    @abstractmethod
    def test__recompute_candidates(self):
        raise NotImplementedError

    @pytest.mark.parametrize("commit, force_change", [(True, False), (False, True)])
    def test__recompute_attributes__sex_field(self, commit, force_change):
        male_related_classifications = DummyClassificationFactory.create_batch(size=3, sex="M")
        female_related_classifications = DummyClassificationFactory.create_batch(size=2, sex="F")
        related_classifications = male_related_classifications + female_related_classifications

        obj = self.factory_cls()
        obj.sex = "F" if force_change else "M"

        with patch(
            f"{self.model.__module__}.{self.model.__name__}.related_classifications",
            new_callable=PropertyMock,
        ) as mocked_related_classficiations:
            with patch.object(obj, "save", return_value=None) as mocked_save:
                mocked_related_classficiations.return_value = related_classifications

                has_changed = obj._recompute_attributes(fields=["sex"], commit=commit)

                if commit and force_change:
                    mocked_save.assert_called_once()
                else:
                    mocked_save.assert_not_called()

        assert has_changed == force_change
        assert obj.sex == "M" if force_change else "F"

    @pytest.mark.parametrize(
        "commit, min_prob, min_taxon_rank, expected_taxon_name,"
        + "expected_probability, expected_return, expected_commit",
        [
            (
                False,  # commit
                0.75,  # min_prob
                None,  # min_taxon_rank
                "class1",  # expected_taxon_name
                Decimal("0.8"),  # expected_probability
                False,  # expected_return
                False,  # expected_commit
            ),
            (
                True,  # commit
                0.75,  # min_prob
                None,  # min_taxon_rank
                "class1",  # expected_taxon_name
                Decimal("0.8"),  # expected_probability
                False,  # expected_return
                False,  # expected_commit
            ),
            (
                False,  # commit
                0.75,  # min_prob
                Taxon.TaxonomicRank.SPECIES,  # min_taxon_rank
                "life",  # expected_taxon_name
                Decimal("1"),  # expected_probability
                True,  # expected_return
                False,  # expected_commit
            ),
            (
                True,  # commit
                0.75,  # min_prob
                Taxon.TaxonomicRank.SPECIES,  # min_taxon_rank
                "life",  # expected_taxon_name
                Decimal("1"),  # expected_probability
                True,  # expected_return
                True,  # expected_commit
            ),
            (
                True,  # commit
                0.7,  # min_prob
                None,  # min_taxon_rank
                "specie1_1",  # expected_taxon_name
                Decimal("0.7"),  # expected_probability
                True,  # expected_return
                True,  # expected_commit
            ),
            (
                True,  # commit
                0.7,  # min_prob
                Taxon.TaxonomicRank.SPECIES,  # min_taxon_rank
                "specie1_1",  # expected_taxon_name
                Decimal("0.7"),  # expected_probability
                True,  # expected_return
                True,  # expected_commit
            ),
        ],
    )
    def test__recompute_label_consensus(
        self,
        taxon_root,
        commit,
        min_prob,
        min_taxon_rank,
        expected_taxon_name,
        expected_probability,
        expected_return,
        expected_commit,
    ):
        # Creating a simple taxonomy tree
        taxon_class1 = TaxonFactory(name="class1", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
        taxon_specie1_1 = TaxonFactory(name="specie1_1", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class1)
        taxon_specie1_2 = TaxonFactory(name="specie1_2", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class1)
        taxon_class2 = TaxonFactory(name="class2", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)

        obj = self.factory_cls(label=taxon_class1, probability=Decimal("0.8"))

        TaxonClassificationCandidateFactory(label=taxon_root, probability=Decimal("1"), content_object=obj),
        TaxonClassificationCandidateFactory(label=taxon_class1, probability=Decimal("0.8"), content_object=obj),
        TaxonClassificationCandidateFactory(label=taxon_specie1_1, probability=Decimal("0.7"), content_object=obj),
        TaxonClassificationCandidateFactory(label=taxon_specie1_2, probability=Decimal("0.1"), content_object=obj),
        TaxonClassificationCandidateFactory(label=taxon_class2, probability=Decimal("0.1"), content_object=obj),

        with patch.object(obj, "save", return_value=None) as mock_method:
            return_result = obj._recompute_label_consensus(
                commit=commit, min_prob=min_prob, min_taxon_rank=min_taxon_rank
            )

            if expected_commit:
                mock_method.assert_called_once()
            else:
                mock_method.assert_not_called()

        assert obj.probability == expected_probability
        assert obj.label.name.lower() == expected_taxon_name.lower()
        assert return_result == expected_return

    # @override
    @pytest.mark.parametrize("commit, from_candidates", [(True, False), (False, True)])
    def test_recompute_result(self, commit, from_candidates):
        manager = Mock()

        obj = self.factory_cls()

        expected_calls = []
        with patch.object(obj, "_recompute_candidates", return_value=None) as mocked_recompute_candidates:
            with patch.object(obj, "_recompute_attributes", return_value=True) as mocked_recompute_attributes:
                with patch.object(
                    obj, "_recompute_label_consensus", return_value=True
                ) as mocked_recompute_label_consensus:
                    with patch.object(obj, "save", return_value=None) as mocked_save:
                        manager.attach_mock(mocked_recompute_candidates, "mocked_recompute_candidates")
                        manager.attach_mock(mocked_recompute_attributes, "mocked_recompute_attributes")
                        manager.attach_mock(mocked_recompute_label_consensus, "mocked_recompute_label_consensus")
                        manager.attach_mock(mocked_save, "mocked_save")

                        obj.recompute_result(commit=commit, from_candidates=from_candidates)

                        if not from_candidates:
                            expected_calls.append(call.mocked_recompute_candidates())

                        expected_calls.append(call.mocked_recompute_attributes(commit=False))
                        expected_calls.append(call.mocked_recompute_label_consensus(commit=False))

                        if commit:
                            expected_calls.append(call.mocked_save())

        manager.assert_has_calls(calls=expected_calls, any_order=False)

    def test__save_sets_label_to_root_if_empty_on_create(self, taxon_root):
        obj = self.factory_cls(label=None)

        assert obj.label == taxon_root
        assert obj.probability == 1


class BaseTestBaseIdentificationTaskResult(BaseTestBaseClassificationTaskResult, BaseTestBaseShape):
    @pytest.mark.parametrize("fieldname", ["points", "shape_type"])
    def test__notify_changes_is_called_on_shape_change(self, fieldname):
        super().assert__notify_changes_is_called_on_field_change(
            fieldname=fieldname,
        )

    # properties
    @abstractmethod
    def test_relevant_photo_identifications(self):
        raise NotImplementedError

    @abstractmethod
    def test_recompute_shape(self):
        raise NotImplementedError

    # methods
    def test_save_sets_default_to_points_if_null(self):
        obj = self.factory_cls(points=None)
        assert obj.points == [[0, 0], [1, 1]]
        assert obj.shape_type == BaseShape.ShapeType.RECTANGLE


@pytest.mark.django_db
class TestIndividualIdentificationTaskResult(BaseTestBaseClassificationTaskResult):
    model = IndividualIdentificationTaskResult
    factory_cls = IndividualIdentificationTaskResultFactory

    task_model = IndividualIdentificationTask
    task_factory_cls = IndividualIdentificationTaskFactory

    # properties
    def test_related_classifications_returns_empty_list_if_no_photo_identification_results(self):
        ind_task_result = self.factory_cls()

        with patch(
            f"{self.model.__module__}.{self.model.__name__}.photo_identification_results",
            new_callable=PropertyMock,
        ) as mocked_photo_identification_results:
            mocked_photo_identification_results.return_value = PhotoIdentificationTaskResult.objects.none()
            assert ind_task_result.related_classifications == []

    @pytest.mark.parametrize("exist_ground_truth", [True, False])
    def test_related_classifications(self, exist_ground_truth):
        ind_task_result = self.factory_cls(type=BaseTaskResult.ResultType.COMMUNITY)

        # Photo ind tasks
        photo_ind_task1 = PhotoIdentificationTaskFactory(task=ind_task_result.task)
        photo_ind_task2 = PhotoIdentificationTaskFactory(task=ind_task_result.task)
        photo_ind_task3_other = PhotoIdentificationTaskFactory()

        yesterday = timezone.now() - timedelta(days=1)
        now = timezone.now()

        result_community1 = PhotoIdentificationTaskResultFactory(
            created_at=yesterday,
            updated_at=yesterday,
            task=photo_ind_task1,
            type=BaseTaskResult.ResultType.COMMUNITY,
            is_ground_truth=exist_ground_truth,
        )
        _ = PhotoIdentificationTaskResultFactory(task=photo_ind_task1, type=BaseTaskResult.ResultType.ENSEMBLED)

        result_community2 = PhotoIdentificationTaskResultFactory(
            created_at=yesterday,
            updated_at=now,
            task=photo_ind_task2,
            type=BaseTaskResult.ResultType.COMMUNITY,
            is_ground_truth=exist_ground_truth,
        )
        _ = PhotoIdentificationTaskResultFactory(task=photo_ind_task2, type=BaseTaskResult.ResultType.COMPUTER_VISION)

        # other community
        _ = PhotoIdentificationTaskResultFactory(task=photo_ind_task3_other, type=BaseTaskResult.ResultType.COMMUNITY)

        # Expected result
        expected_result = [result_community2]
        if not exist_ground_truth:
            expected_result = [result_community1, result_community2]

        assert frozenset(ind_task_result.related_classifications) == frozenset(expected_result)

    def test_photo_identification_results(self):
        ind_task_result = self.factory_cls(type=BaseTaskResult.ResultType.COMMUNITY)

        # Photo ind tasks
        photo_ind_task1 = PhotoIdentificationTaskFactory(task=ind_task_result.task)
        photo_ind_task2 = PhotoIdentificationTaskFactory(task=ind_task_result.task)
        photo_ind_task3_other = PhotoIdentificationTaskFactory()

        result_community1 = PhotoIdentificationTaskResultFactory(
            task=photo_ind_task1, type=BaseTaskResult.ResultType.COMMUNITY
        )
        _ = PhotoIdentificationTaskResultFactory(task=photo_ind_task1, type=BaseTaskResult.ResultType.ENSEMBLED)

        result_community2 = PhotoIdentificationTaskResultFactory(
            task=photo_ind_task2, type=BaseTaskResult.ResultType.COMMUNITY
        )
        _ = PhotoIdentificationTaskResultFactory(task=photo_ind_task2, type=BaseTaskResult.ResultType.COMPUTER_VISION)

        # Other community
        _ = PhotoIdentificationTaskResultFactory(task=photo_ind_task3_other, type=BaseTaskResult.ResultType.COMMUNITY)

        assert frozenset(ind_task_result.photo_identification_results) == frozenset(
            [result_community1, result_community2]
        )

    # methods
    def test__recompute_candidates_use_related_classifications_property(self):
        obj = self.factory_cls()

        with patch(
            f"{self.model.__module__}.{self.model.__name__}.related_classifications",
            new_callable=PropertyMock,
        ) as mocked_related_classifications:
            mocked_related_classifications.return_value = []
            with patch.object(obj, "update_candidates_from_tree", return_value=False):
                _ = obj._recompute_candidates()

                mocked_related_classifications.assert_called_once_with()

    @pytest.mark.parametrize("mock_changes", [True, False])
    def test__recompute_candidates_when_empty_related_classifications(self, mock_changes):
        obj = self.factory_cls()

        with patch(
            f"{self.model.__module__}.{self.model.__name__}.related_classifications",
            new_callable=PropertyMock,
        ) as mocked_related_classifications:
            mocked_related_classifications.return_value = []
            with patch.object(
                obj, "update_candidates_from_tree", return_value=mock_changes
            ) as mocked_update_candidates_from_tree:
                has_changed = obj._recompute_candidates()

                mocked_update_candidates_from_tree.assert_called_once_with(tree=None)

                assert has_changed is mock_changes

    @pytest.mark.parametrize("correct_initial_candidates, expected_return", [(True, False), (False, True)])
    def test__recompute_candidates(self, taxon_root, correct_initial_candidates, expected_return):
        # Creating a simple taxonomy tree
        taxon_class1 = TaxonFactory(name="class1", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
        taxon_specie1_1 = TaxonFactory(name="specie1_1", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class1)
        taxon_specie1_2 = TaxonFactory(name="specie1_2", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class1)
        taxon_class2 = TaxonFactory(name="class2", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
        _ = TaxonFactory(name="specie2_1", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class2)

        # Weight each photo by the number of identifications that have contributed.
        candidates = []

        if correct_initial_candidates:
            candidates = [
                TaxonClassificationCandidateFactory(label=taxon_root, probability=Decimal("1")),
                TaxonClassificationCandidateFactory(label=taxon_class1, probability=Decimal("1")),
                TaxonClassificationCandidateFactory(label=taxon_specie1_1, probability=Decimal("0.25")),
                TaxonClassificationCandidateFactory(label=taxon_specie1_2, probability=Decimal("0.75")),
            ]

        ind_task_result = self.factory_cls(type=BaseTaskResult.ResultType.COMMUNITY)

        # Photo ind tasks
        photo_ind_task1 = PhotoIdentificationTaskFactory(task=ind_task_result.task)
        photo_ind_task2 = PhotoIdentificationTaskFactory(task=ind_task_result.task)

        # Create 3 user identification for task1
        ui_1 = UserIdentificationFactory.create_batch(
            size=3,
            task=photo_ind_task1,
            points=[[0, 0], [1, 1]],
            shape_type=BaseShape.ShapeType.RECTANGLE,
        )
        for ui in ui_1:
            TaxonClassificationCandidateFactory(
                label=taxon_specie1_2, probability=Decimal("0.75"), is_seed=True, content_object=ui
            )
            ui.recompute_candidates_tree()

        # Create 1 predictions for task 1
        p_1 = PredictionFactory(
            task=photo_ind_task1, points=[[0, 0], [1, 1]], shape_type=BaseShape.ShapeType.RECTANGLE
        )
        TaxonClassificationCandidateFactory(
            label=taxon_specie1_2, probability=Decimal("1"), is_seed=True, content_object=p_1
        )
        p_1.recompute_candidates_tree()

        # Create 1 predictions for task 2
        _ = PredictionFactory(task=photo_ind_task2, points=[[0, 0], [1, 1]], shape_type=BaseShape.ShapeType.RECTANGLE)

        # Call method
        ind_task_result.candidates.set(candidates)

        result = ind_task_result._recompute_candidates()

        assert result == expected_return

        # Expected new candidates
        expected_tree_root = TaxonProbNode(
            probability=1,
            taxon=taxon_root,
            children=[
                TaxonProbNode(
                    probability=1,
                    taxon=taxon_class1,
                    children=[
                        TaxonProbNode(probability=0.25, taxon=taxon_specie1_1),
                        TaxonProbNode(probability=0.75, taxon=taxon_specie1_2),
                    ],
                ),
            ],
        )

        assert ind_task_result.get_classification_tree().to_dict == expected_tree_root.to_dict


@pytest.mark.django_db
class TestPhotoIdentificationTaskResult(BaseTestBaseIdentificationTaskResult):
    model = PhotoIdentificationTaskResult
    factory_cls = PhotoIdentificationTaskResultFactory

    task_factory_cls = PhotoIdentificationTaskFactory
    task_model = PhotoIdentificationTask

    # classmethods
    @pytest.mark.parametrize(
        "type, expected_result",
        [
            (BaseTaskResult.ResultType.COMMUNITY, (UserIdentification,)),
            (BaseTaskResult.ResultType.COMPUTER_VISION, (Prediction,)),
            (BaseTaskResult.ResultType.ENSEMBLED, (UserIdentification, Prediction, ExternalIdentification)),
            (BaseTaskResult.ResultType.EXTERNAL, (ExternalIdentification,)),
        ],
    )
    def test_get_identification_classes_by_type(self, type, expected_result):
        assert self.model.get_identification_classes_by_type(type=type) == expected_result

    @pytest.mark.parametrize(
        "type, expected_result",
        [
            (BaseTaskResult.ResultType.COMMUNITY, {UserIdentification: 1}),
            (BaseTaskResult.ResultType.COMPUTER_VISION, {Prediction: 1}),
            (
                BaseTaskResult.ResultType.ENSEMBLED,
                {UserIdentification: 0.65, Prediction: 0.25, ExternalIdentification: 0.1},
            ),
            (BaseTaskResult.ResultType.EXTERNAL, {ExternalIdentification: 1}),
        ],
    )
    def test_get_identification_classes_weights_by_type(self, type, expected_result):
        assert self.model.get_identification_classes_weights_by_type(type=type) == expected_result

    @pytest.mark.parametrize("type", BaseTaskResult.ResultType.values)
    def test_get_normalized_weights_by_type(self, type):
        class_to_test = UserIdentification
        if class_to_test in self.model.get_identification_classes_by_type(type=type):
            expected_result = {UserIdentification: 1}
        else:
            expected_result = {}

        assert self.model.get_normalized_weights_by_type(type, classes_in_use=[class_to_test]) == expected_result

    # fields
    def test_user_identifications_points_to_UserIdentification(self):
        assert self.model.user_identifications.field.related_model is UserIdentification

    def test_user_identifications_is_not_editable(self):
        assert not self.model._meta.get_field("user_identifications").editable

    def test_predictions_points_to_Prediction(self):
        assert self.model.predictions.field.related_model is Prediction

    def test_predictions_is_not_editable(self):
        assert not self.model._meta.get_field("predictions").editable

    def test_external_identifications_points_to_ExternalIdentification(self):
        assert self.model.external_identifications.field.related_model is ExternalIdentification

    def test_external_identifications_is_not_editable(self):
        assert not self.model._meta.get_field("external_identifications").editable

    def test_is_ground_truth_can_not_be_null(self):
        assert not self.model._meta.get_field("is_ground_truth").null

    def test_is_ground_truth_default_False(self):
        assert not self.model._meta.get_field("is_ground_truth").default

    def test_is_ground_truth_is_not_editable(self):
        assert not self.model._meta.get_field("is_ground_truth").editable

    # properties
    @pytest.mark.parametrize("type", BaseTaskResult.ResultType.values)
    def test_relevant_photo_identifications(self, type):
        obj = self.factory_cls(type=type)

        # User identifications
        user_iden = UserIdentificationFactory(task=obj.task)

        # User identifications skipped (not finised)
        _ = UserIdentificationFactory(task=obj.task, was_skipped=True)

        # Prediction
        pred = PredictionFactory(task=obj.task)

        # External Identification
        ext = ExternalIdentificationFactory(task=obj.task)

        identification_candidates = [user_iden, pred, ext]
        expected_identifications_called = list(
            filter(lambda x: isinstance(x, obj.identification_classes), identification_candidates)
        )

        with patch.object(obj, "_get_relevant_photo_identifications", return_value=None) as mocked_method:
            obj.relevant_photo_identifications

            mocked_method.assert_called_once_with(identifications=expected_identifications_called)

    def test_identification_classes(self):
        obj = self.factory_cls.build()

        with patch.object(obj, "get_identification_classes_by_type", return_value=None) as mocked_method:
            obj.identification_classes

            mocked_method.assert_called_once_with(type=obj.type)

    def test_inter_identification_aggr_weights(self):
        obj = self.factory_cls.build()

        with patch.object(obj, "get_identification_classes_weights_by_type", return_value=None) as mocked_method:
            obj.inter_identification_aggr_weights

            mocked_method.assert_called_once_with(type=obj.type)

    def test_num_contributions(self):
        obj = self.factory_cls.build()

        with patch(
            f"{self.model.__module__}.{self.model.__name__}.related_classifications",
            new_callable=PropertyMock,
        ) as mocked_related_classficiations:
            mocked_related_classficiations.return_value = [1, 2, 3]
            assert obj.num_contributions == 3

    def test_related_classifications(self):
        obj = self.factory_cls()

        # User identifications
        user_iden = UserIdentificationFactory(task=obj.task)

        # Prediction
        pred = PredictionFactory(task=obj.task)

        # External Identification
        ext = ExternalIdentificationFactory(task=obj.task)

        obj.user_identifications.set([user_iden])
        obj.predictions.set([pred])
        obj.external_identifications.set([ext])

        assert obj.related_classifications == [user_iden, pred, ext]

    # methods
    def test__average_photo_identifications_by_model(self, taxon_root):
        # Creating a simple taxonomy tree
        taxon_class1 = TaxonFactory(name="class1", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
        taxon_specie1_1 = TaxonFactory(name="specie1_1", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class1)
        taxon_specie1_2 = TaxonFactory(name="specie1_2", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class1)
        taxon_class2 = TaxonFactory(name="class2", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
        # Needed to know that does not expand.
        _ = TaxonFactory(name="specie2_1", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class2)

        # User identifications
        ui_1 = UserIdentificationFactory()
        TaxonClassificationCandidateFactory(label=taxon_specie1_1, probability=1, content_object=ui_1, is_seed=True)
        ui_1.recompute_candidates_tree()

        ui_2 = UserIdentificationFactory()
        TaxonClassificationCandidateFactory(label=taxon_specie1_1, probability=0.5, content_object=ui_2, is_seed=True)
        ui_2.recompute_candidates_tree()

        expected_ui_result = TaxonProbNodeFactory(
            taxon=taxon_root,
            probability=1,
            children=[
                TaxonProbNodeFactory(
                    taxon=taxon_class1,
                    probability=1,
                    children=[
                        TaxonProbNodeFactory(taxon=taxon_specie1_1, probability=0.75),
                        TaxonProbNodeFactory(taxon=taxon_specie1_2, probability=0.25),
                    ],
                ),
            ],
        )

        # Predictinos
        p_1 = PredictionFactory()
        TaxonClassificationCandidateFactory(label=taxon_specie1_1, probability=1, content_object=p_1, is_seed=True)
        p_1.recompute_candidates_tree()

        p_2 = PredictionFactory()
        TaxonClassificationCandidateFactory(label=taxon_specie1_1, probability=0.5, content_object=p_2, is_seed=True)
        p_2.recompute_candidates_tree()

        # Get last by updated_at
        expected_p_result = TaxonProbNodeFactory(
            taxon=taxon_root,
            probability=1,
            children=[
                TaxonProbNodeFactory(
                    taxon=taxon_class1,
                    probability=1,
                    children=[
                        TaxonProbNodeFactory(taxon=taxon_specie1_1, probability=0.5),
                        TaxonProbNodeFactory(taxon=taxon_specie1_2, probability=0.5),
                    ],
                ),
            ],
        )

        # External classifications
        ext_1 = ExternalIdentificationFactory()
        TaxonClassificationCandidateFactory(label=taxon_specie1_1, probability=1, content_object=ext_1, is_seed=True)
        ext_1.recompute_candidates_tree()

        ext_2 = ExternalIdentificationFactory()
        TaxonClassificationCandidateFactory(label=taxon_specie1_1, probability=0.5, content_object=ext_2, is_seed=True)
        ext_2.recompute_candidates_tree()

        expected_ext_result = TaxonProbNodeFactory(
            taxon=taxon_root,
            probability=1,
            children=[
                TaxonProbNodeFactory(
                    taxon=taxon_class1,
                    probability=1,
                    children=[
                        TaxonProbNodeFactory(taxon=taxon_specie1_1, probability=0.75),
                        TaxonProbNodeFactory(taxon=taxon_specie1_2, probability=0.25),
                    ],
                ),
            ],
        )

        photo_identifications = [ui_1, ui_2, p_1, p_2, ext_1, ext_2]
        random.shuffle(photo_identifications)

        result_dict = self.model._average_photo_identifications_by_model(photo_identifications=photo_identifications)

        assert result_dict[UserIdentification].to_dict == expected_ui_result.to_dict
        assert result_dict[Prediction].to_dict == expected_p_result.to_dict
        assert result_dict[ExternalIdentification].to_dict == expected_ext_result.to_dict

    @pytest.mark.parametrize("type", BaseTaskResult.ResultType.values)
    def test__get_relevant_photo_identifications(self, type):
        obj = self.factory_cls.build(type=type)

        # User identifications
        user_iden = UserIdentificationFactory()

        # Prediction
        pred = PredictionFactory()

        # External Identification
        ext = ExternalIdentificationFactory()

        identification_candidates = [user_iden, pred, ext]
        expected_identifications_called = list(
            filter(lambda x: isinstance(x, obj.identification_classes), identification_candidates)
        )

        assert (
            obj._get_relevant_photo_identifications(identifications=identification_candidates)
            == expected_identifications_called
        )

        # Adding Ground truth
        user_iden_gt = UserIdentificationFactory(is_ground_truth=True)

        identification_candidates += [user_iden_gt]
        if UserIdentification in obj.identification_classes:
            expected_identifications_called = [user_iden_gt]

        assert (
            obj._get_relevant_photo_identifications(identifications=identification_candidates)
            == expected_identifications_called
        )

        # First user identification is updated to ground_truth
        user_iden.is_ground_truth = True
        user_iden.save()

        assert user_iden_gt.updated_at < user_iden.updated_at

        if UserIdentification in obj.identification_classes:
            expected_identifications_called = [user_iden]

        assert (
            obj._get_relevant_photo_identifications(identifications=identification_candidates)
            == expected_identifications_called
        )

    def test__get_resulting_identification_tree_returns_TaxonProbNode_root_if_not_normalized_weights(self, taxon_root):
        obj = self.factory_cls()

        with patch.object(obj, "_average_photo_identifications_by_model", return_value={}):
            with patch.object(obj, "get_normalized_weights_by_type", return_value={}):
                assert (
                    obj._get_resulting_identification_tree().to_dict
                    == TaxonProbNodeFactory(taxon=taxon_root, probability=1).to_dict
                )

    def test__get_resulting_identification_tree(self, taxon_root):
        # Creating a simple taxonomy tree
        taxon_class1 = TaxonFactory(name="class1", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
        taxon_class2 = TaxonFactory(name="class2", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)

        obj = self.factory_cls()

        grouped_trees = {
            UserIdentification: TaxonProbNodeFactory(
                taxon=taxon_root, probability=1, children=[TaxonProbNodeFactory(taxon=taxon_class1, probability=1)]
            ),
            Prediction: TaxonProbNodeFactory(
                taxon=taxon_root,
                probability=1,
                children=[
                    TaxonProbNodeFactory(taxon=taxon_class1, probability=0.5),
                    TaxonProbNodeFactory(taxon=taxon_class2, probability=0.5),
                ],
            ),
            ExternalIdentification: TaxonProbNodeFactory(
                taxon=taxon_root, probability=1, children=[TaxonProbNodeFactory(taxon=taxon_class1, probability=1)]
            ),
        }
        normalized_weights = {UserIdentification: 0.5, Prediction: 0.3, ExternalIdentification: 0.2}

        expected_result = TaxonProbNode(
            taxon=taxon_root,
            probability=1,
            children=[
                TaxonProbNode(taxon=taxon_class1, probability=0.85),
                TaxonProbNode(taxon=taxon_class2, probability=0.15),
            ],
        )

        with patch.object(obj, "_average_photo_identifications_by_model", return_value=grouped_trees):
            with patch.object(obj, "get_normalized_weights_by_type", return_value=normalized_weights):
                assert obj._get_resulting_identification_tree().to_dict == expected_result.to_dict

    def test__recompute_candidates(self):
        obj = self.factory_cls()

        manager = Mock()
        with patch.object(obj, "_recompute_shape", return_value=True) as mocked_shape:
            with patch.object(obj, "_get_resulting_identification_tree", return_value="tree"):
                with patch.object(obj, "update_is_ground_truth", return_value=None) as mocked_updated_ground_truth:
                    with patch.object(
                        obj, "update_candidates_from_tree", return_value=False
                    ) as mocked_update_candidates:
                        manager.attach_mock(mocked_shape, "mocked_shape")
                        manager.attach_mock(mocked_updated_ground_truth, "mocked_updated_ground_truth")
                        manager.attach_mock(mocked_update_candidates, "mocked_update_candidates")
                        has_changed = obj._recompute_candidates()

                        assert has_changed is True
                        manager.assert_has_calls(
                            calls=[
                                call.mocked_shape(commit=True),
                                call.mocked_updated_ground_truth(commit=True),
                                call.mocked_update_candidates(tree="tree"),
                            ],
                            any_order=False,
                        )

    @pytest.mark.parametrize("commit", [True, False])
    def test_recompute_shape(self, commit):
        obj = self.factory_cls(shape_type=BaseShape.ShapeType.RECTANGLE, points=[[0.3, 0.3], [0.4, 0.4]])

        assert not obj.user_identifications.exists()
        assert not obj.predictions.exists()
        assert not obj.external_identifications.exists()

        with patch(
            f"{self.model.__module__}.{self.model.__name__}.relevant_photo_identifications",
            new_callable=PropertyMock,
        ) as mocked_relevant_photo_identifications:
            with patch.object(obj, "save") as mocked_save:
                ui_1 = UserIdentificationFactory(points=[[0, 0], [0.5, 0.5]], shape_type=BaseShape.ShapeType.RECTANGLE)
                ui_2 = UserIdentificationFactory(
                    points=[[0, 0], [0.49, 0.49]], shape_type=BaseShape.ShapeType.RECTANGLE
                )
                pred = PredictionFactory(points=[[0.3, 0.3], [0.4, 0.4]], shape_type=BaseShape.ShapeType.RECTANGLE)
                mocked_relevant_photo_identifications.return_value = [ui_1, ui_2, pred]

                has_changed = obj._recompute_shape(commit=commit)

                assert has_changed
                assert obj.points == ((0, 0), (0.495, 0.495))
                assert frozenset(obj.user_identifications.all()) == frozenset([ui_1, ui_2])
                assert not obj.predictions.exists()
                assert not obj.external_identifications.exists()

            if commit:
                mocked_save.assert_called_once()
            else:
                mocked_save.assert_not_called()

    @pytest.mark.parametrize("commit", [True, False])
    def test_recompute_shape_with_no_changes(self, commit):
        obj = self.factory_cls(shape_type=BaseShape.ShapeType.RECTANGLE, points=[[0.3, 0.3], [0.4, 0.4]])

        with patch(
            f"{self.model.__module__}.{self.model.__name__}.relevant_photo_identifications",
            new_callable=PropertyMock,
        ) as mocked_relevant_photo_identifications:
            with patch.object(obj, "save") as mocked_save:
                mocked_relevant_photo_identifications.return_value = [
                    UserIdentificationFactory(
                        points=[[0.3, 0.3], [0.4, 0.4]], shape_type=BaseShape.ShapeType.RECTANGLE
                    )
                ]
                has_changed = obj._recompute_shape(commit=commit)

                assert not has_changed
                mocked_save.assert_not_called()

    @pytest.mark.parametrize("commit", [True, False])
    def test_recompute_shape_same_number_of_identification_must_use_user_only(self, commit):
        obj = self.factory_cls(shape_type=BaseShape.ShapeType.RECTANGLE, points=[[0.3, 0.3], [0.4, 0.4]])

        with patch(
            f"{self.model.__module__}.{self.model.__name__}.relevant_photo_identifications",
            new_callable=PropertyMock,
        ) as mocked_relevant_photo_identifications:
            with patch.object(obj, "save") as mocked_save:
                mocked_relevant_photo_identifications.return_value = [
                    UserIdentificationFactory(points=[[0, 0], [0.5, 0.5]], shape_type=BaseShape.ShapeType.RECTANGLE),
                    ExternalIdentificationFactory(
                        points=[[0, 0], [0.8, 0.8]], shape_type=BaseShape.ShapeType.RECTANGLE
                    ),
                    PredictionFactory(points=[[0.3, 0.3], [0.4, 0.4]], shape_type=BaseShape.ShapeType.RECTANGLE),
                ]

                obj._recompute_shape(commit=commit)

                assert obj.points == ((0, 0), (0.5, 0.5))

            if commit:
                mocked_save.assert_called_once()
            else:
                mocked_save.assert_not_called()

    def test__recompute_shape_with_empty_identifications(self):
        obj = self.factory_cls(shape_type=BaseShape.ShapeType.RECTANGLE, points=[[0.3, 0.3], [0.4, 0.4]])

        obj.user_identifications.set([UserIdentificationFactory()])

        assert obj.user_identifications.exists()

        with patch(
            f"{self.model.__module__}.{self.model.__name__}.relevant_photo_identifications",
            new_callable=PropertyMock,
        ) as mocked_relevant_photo_identifications:
            mocked_relevant_photo_identifications.return_value = []

            obj._recompute_shape(commit=True)

            assert obj.points == ((0, 0), (1, 1))
            assert obj.shape_type == BaseShape.ShapeType.RECTANGLE
            assert not obj.user_identifications.exists()

    @pytest.mark.parametrize("type", BaseTaskResult.ResultType.values)
    def test__update_is_ground_truth_sets_is_ground_truth_if_ground_truth_identifications_considered(self, type):
        obj = self.factory_cls(type=type)

        assert not obj.is_ground_truth

        # Adding 1 ground_truth classification
        ui = UserIdentificationFactory(task=obj.task, is_ground_truth=True)

        obj.user_identifications.set([ui])
        has_changed = obj.update_is_ground_truth()

        assert obj.is_ground_truth == bool(type is BaseTaskResult.ResultType.COMMUNITY.value)
        assert has_changed == bool(type is BaseTaskResult.ResultType.COMMUNITY.value)

    # meta
    def test_constraint_unique_ground_truth_per_task(self):
        task = self.task_factory_cls()

        self.factory_cls(is_ground_truth=False, task=task, type=BaseTaskResult.ResultType.COMMUNITY)

        with pytest.raises(IntegrityError, match=r"unique constraint"):
            self.factory_cls(is_ground_truth=True, task=task, type=BaseTaskResult.ResultType.COMMUNITY)

    @pytest.mark.parametrize("type", BaseTaskResult.ResultType.values)
    def test_constraint_only_ground_truth_is_allowed_for_community_type(self, type):
        expected_raise = (
            does_not_raise()
            if type == BaseTaskResult.ResultType.COMMUNITY
            else pytest.raises(IntegrityError, match=r"check constraint")
        )
        with expected_raise:
            self.factory_cls(is_ground_truth=True, type=type)
