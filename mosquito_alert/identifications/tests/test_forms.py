from decimal import Decimal

import pytest

from ..forms import TaxonClassificationCandidateForm, TaxonClassificationCategorizedProbabilityCandidateForm
from .factories import TaxonClassificationCandidateFactory


@pytest.mark.django_db
class TestTaxonClassificationCandidateForm:
    form_cls = TaxonClassificationCandidateForm

    def test_is_seed_is_True_by_default(self):
        form = self.form_cls()
        assert form.fields["is_seed"].initial is True

    def test_is_seed_is_disabled_by_default(self):
        form = self.form_cls()

        assert form.fields["is_seed"].disabled is True

    def test_if_object_already_exists_and_is_not_seed_disable_all_fields(self):
        form = self.form_cls(instance=TaxonClassificationCandidateFactory(is_seed=False))

        assert all([form.fields[x].disabled for x in form.fields])

    def test_if_object_not_exists_and_not_disable_all_fields(self):
        form = self.form_cls()

        assert not all([form.fields[x].disabled for x in form.fields])

    def test_fields_displayed(self):
        assert self.form_cls._meta.fields == ["label", "probability", "is_seed"]

    def test_probability_valid_range_is_0_to_1(self):
        form = self.form_cls()
        assert form.fields["probability"].widget.attrs["max"] == "1"
        assert form.fields["probability"].widget.attrs["min"] == "0"


@pytest.mark.django_db
class TestTaxonClassificationCategorizedProbabilityCandidateForm(TestTaxonClassificationCandidateForm):
    form_cls = TaxonClassificationCategorizedProbabilityCandidateForm

    # @override
    def test_probability_valid_range_is_0_to_1(self):
        pass

    def test_probability_is_humanized_if_instance_is_seed(self):
        form = self.form_cls(instance=TaxonClassificationCandidateFactory(is_seed=True))

        assert form.fields["probability"].choices == [("1.0", "I'm sure"), ("0.75", "I'm doubting")]

    def test_probability_if_new_instance(self):
        form = self.form_cls()

        assert form.fields["probability"].choices == [("1.0", "I'm sure"), ("0.75", "I'm doubting")]

    def test_probability_is_required_if_instance_is_seed(self):
        form = self.form_cls(instance=TaxonClassificationCandidateFactory(is_seed=True))

        assert form.fields["probability"].required

    def test_probability_is_cast_to_decimal_if_instance_is_seed(self):
        form = self.form_cls(instance=TaxonClassificationCandidateFactory(is_seed=True))

        assert form.fields["probability"].coerce == Decimal
