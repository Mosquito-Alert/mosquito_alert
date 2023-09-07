from unittest.mock import Mock, patch

import pytest
from django.contrib.contenttypes.forms import generic_inlineformset_factory

from ..formsets import TaxonClassificationCandidateFormSet
from ..models import TaxonClassificationCandidate
from .factories import TaxonClassificationCandidateFactory, UserIdentificationFactory


@pytest.mark.django_db
class TestTaxonClassificationCandidateFormSet:
    formset_cls = TaxonClassificationCandidateFormSet

    @pytest.fixture
    def formset(self):
        return generic_inlineformset_factory(model=TaxonClassificationCandidate, formset=self.formset_cls)()

    @pytest.mark.parametrize(
        "has_changed, commit, expected_has_called",
        [(True, True, True), (True, False, False), (False, True, False), (False, False, False)],
    )
    def test_save_calls_recompute_candidates_if_detect_changes_and_commit(
        self, formset, has_changed, commit, expected_has_called
    ):
        mocked_instance = Mock()

        with patch.object(formset, "has_changed", return_value=has_changed):
            with patch("nested_admin.formsets.NestedInlineFormSetMixin.save", return_value=None):
                formset.instance = mocked_instance

                formset.save(commit=commit)

                if expected_has_called:
                    mocked_instance.recompute_candidates_tree.assert_called_once()
                else:
                    mocked_instance.recompute_candidates_tree.assert_not_called()

    def test_save_delete_all_candidates_that_are_not_seed_before_saving(self, formset):
        instance = UserIdentificationFactory()

        _ = TaxonClassificationCandidateFactory(content_object=instance, is_seed=True)
        _ = TaxonClassificationCandidateFactory(content_object=instance, is_seed=False)

        assert instance.candidates.filter(is_seed=False).exists()

        with patch.object(formset, "has_changed", return_value=True):
            with patch("nested_admin.formsets.NestedInlineFormSetMixin.save", return_value=None):
                formset.instance = instance

                formset.save(commit=False)

        instance.refresh_from_db()
        assert not instance.candidates.filter(is_seed=False).exists()

    def test_save_does_nothing_if_instance_does_not_exist(self, formset):
        instance = UserIdentificationFactory()

        with patch.object(formset, "has_changed", return_value=True):
            with patch("nested_admin.formsets.NestedInlineFormSetMixin.save", return_value=None):
                formset.instance = instance
                instance.delete()

                formset.save(commit=True)

    @pytest.mark.parametrize("is_nested", [True, False])
    def test_save_changes_update_candidate_tree(self, formset, taxon_specie, is_nested):
        instance = UserIdentificationFactory()
        _ = TaxonClassificationCandidateFactory(content_object=instance, is_seed=True, taxon=taxon_specie)

        with patch.object(formset, "has_changed", return_value=True):
            formset.instance = instance
            formset.is_nested = is_nested

            with patch("nested_admin.formsets.NestedInlineFormSetMixin.save", return_value=None):
                with patch.object(instance, "_run_on_notify_changes_to_parent", return_value=None) as mocked_method:
                    formset.save(commit=True)

                    if is_nested:
                        mocked_method.assert_not_called()
                    else:
                        mocked_method.assert_called_once()
