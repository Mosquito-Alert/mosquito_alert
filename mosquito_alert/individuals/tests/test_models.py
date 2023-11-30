from unittest.mock import PropertyMock, patch

import pytest

from mosquito_alert.identifications.models import BaseTaskResult
from mosquito_alert.identifications.tests.factories import (
    IndividualIdentificationTaskResultFactory,
    PhotoIdentificationTaskResultFactory,
)

from ..models import Individual
from .factories import IndividualFactory


@pytest.mark.django_db
class TestIndividual:
    model = Individual
    factory_cls = IndividualFactory

    # classmethods
    def test__get_default_identification_result_type_is_ENSEMBLED(self):
        assert self.model._get_default_identification_result_type() == BaseTaskResult.ResultType.ENSEMBLED

    # properties
    def test_default_identification_result(self):
        obj = self.factory_cls.build()

        with patch.object(obj, "get_identification_result_by_type") as mocked_method:
            obj.default_identification_result

            mocked_method.assert_called_once_with(type=BaseTaskResult.ResultType.ENSEMBLED)

    def test_is_identified(self, taxon_root, taxon_specie):
        obj = self.factory_cls.build()

        with patch(f"{self.model.__module__}.{self.model.__name__}.taxon", new_callable=PropertyMock) as mocked_taxon:
            mocked_taxon.return_value = None
            assert not obj.is_identified

            mocked_taxon.return_value = taxon_root
            assert not obj.is_identified

            mocked_taxon.return_value = taxon_specie
            assert obj.is_identified

    def test_taxon_is_none_when_no_result_found(self):
        obj = self.factory_cls()

        assert obj.taxon is None

    def test_taxon_is_same_as_ensembled_result(self):
        obj = self.factory_cls()

        i_result = IndividualIdentificationTaskResultFactory(
            type=BaseTaskResult.ResultType.ENSEMBLED, task=obj.identification_task
        )

        assert obj.taxon == i_result.taxon

    def test_photos_calls_get_photos_by_identification_result_type(self):
        obj = self.factory_cls.build()

        with patch.object(obj, "get_photos_by_identification_result_type") as mocked_method:
            obj.photos

            mocked_method.assert_called_once_with(type=BaseTaskResult.ResultType.ENSEMBLED)

    # objects
    def test_filter_by_taxon(self, taxon_root, taxon_specie):
        i_result0 = IndividualIdentificationTaskResultFactory(
            type=BaseTaskResult.ResultType.ENSEMBLED, label=taxon_root
        )
        i_result1 = IndividualIdentificationTaskResultFactory(
            type=BaseTaskResult.ResultType.ENSEMBLED, label=taxon_specie
        )
        i_result2 = IndividualIdentificationTaskResultFactory(
            type=BaseTaskResult.ResultType.ENSEMBLED, label=taxon_specie
        )
        # Other cases
        _ = IndividualIdentificationTaskResultFactory(type=BaseTaskResult.ResultType.COMMUNITY, label=taxon_specie)

        assert frozenset(self.model.objects.filter_by_taxon(taxon=taxon_specie).all()) == frozenset(
            [i_result1.task.individual, i_result2.task.individual]
        )
        assert frozenset(
            self.model.objects.filter_by_taxon(taxon=taxon_root, include_descendants=True).all()
        ) == frozenset([i_result0.task.individual, i_result1.task.individual, i_result2.task.individual])

    # methods
    def test_get_photos_by_identification_result_type(self):
        obj = self.factory_cls()

        # Ensembled Results from photos that are for this individual
        p1_result = PhotoIdentificationTaskResultFactory(
            type=BaseTaskResult.ResultType.ENSEMBLED, task__task=obj.identification_task
        )
        p2_result = PhotoIdentificationTaskResultFactory(
            type=BaseTaskResult.ResultType.ENSEMBLED, task__task=obj.identification_task
        )

        # Community result from photo that are for this individual
        _ = PhotoIdentificationTaskResultFactory(
            type=BaseTaskResult.ResultType.COMMUNITY, task__task=obj.identification_task
        )

        # Other photos from other individuals
        _ = PhotoIdentificationTaskResultFactory()

        assert frozenset(
            obj.get_photos_by_identification_result_type(type=BaseTaskResult.ResultType.ENSEMBLED)
        ) == frozenset(
            [
                p1_result.task.photo,
                p2_result.task.photo,
            ]
        )

    def test_get_identification_result_by_type(self):
        obj = self.factory_cls()

        # Identification ensembled result for this individual
        ens_result = IndividualIdentificationTaskResultFactory(
            type=BaseTaskResult.ResultType.ENSEMBLED, task=obj.identification_task
        )
        # Identification Community result for this individual
        _ = IndividualIdentificationTaskResultFactory(
            type=BaseTaskResult.ResultType.COMMUNITY, task=obj.identification_task
        )

        # Other identifications results from other individuals
        _ = IndividualIdentificationTaskResultFactory()

        assert obj.get_identification_result_by_type(type=BaseTaskResult.ResultType.ENSEMBLED) == ens_result
        assert obj.get_identification_result_by_type(type=BaseTaskResult.ResultType.COMPUTER_VISION) is None

    def test__str___with_taxon_defined(self, taxon_specie):
        obj = self.factory_cls()

        _ = IndividualIdentificationTaskResultFactory(
            label=taxon_specie, type=BaseTaskResult.ResultType.ENSEMBLED, task=obj.identification_task
        )

        assert obj.__str__() == taxon_specie.__str__()

    def test__str___with_no_taxon_defined(self):
        obj = self.factory_cls()

        with patch(f"{self.model.__module__}.{self.model.__name__}.taxon", new_callable=PropertyMock) as mocked_taxon:
            mocked_taxon.return_value = None

            assert obj.__str__() == f"Not-identified individual (id={obj.pk})"
