from unittest.mock import patch

import pytest

from mosquito_alert.identifications.models import BaseTaskResult
from mosquito_alert.identifications.tests.factories import (
    PhotoIdentificationTaskFactory,
    PhotoIdentificationTaskResultFactory,
)
from mosquito_alert.images.tests.factories import PhotoFactory
from mosquito_alert.individuals.tests.factories import IndividualFactory
from mosquito_alert.reports.models import IndividualReport

from ..signals import add_new_individual_to_report
from .factories import IndividualReportFactory


def test_add_new_individual_to_report_does_nothing_if_not_create():
    with patch(f"{IndividualReport.__module__}.{IndividualReport.__name__}.individuals") as mocked_add:
        add_new_individual_to_report(sender=None, instance=object, created=False)

        mocked_add.assert_not_called()


@pytest.mark.django_db
def test_indivdidual_is_linked_to_report_on_PhotoIdentificationTask_created():
    photo = PhotoFactory()
    report = IndividualReportFactory(photos=[photo])

    assert not report.individuals.exists()

    photo_task = PhotoIdentificationTaskFactory(photo=photo)

    assert list(report.individuals.all()) == [photo_task.task.individual]


@pytest.mark.django_db
def test_indivdidual_is_not_linked_to_report_if_already_linked_on_PhotoIdentificationTask_created():
    photo = PhotoFactory()
    individual = IndividualFactory()
    report = IndividualReportFactory(photos=[photo], individuals=[individual])

    assert list(report.individuals.all()) == [individual]

    _ = PhotoIdentificationTaskFactory(photo=photo, task=individual.identification_task)

    assert list(report.individuals.all()) == [individual]


@pytest.mark.django_db
def test_individual_is_not_unlinked_from_report_if_other_photos_still():
    photo1 = PhotoFactory()
    photo2 = PhotoFactory()
    individual = IndividualFactory()
    report = IndividualReportFactory(photos=[photo1, photo2], individuals=[individual])

    photo_task1 = PhotoIdentificationTaskFactory(photo=photo1, task=individual.identification_task)
    photo_task2 = PhotoIdentificationTaskFactory(photo=photo2, task=individual.identification_task)

    # Need to add ENSEMBLED result to make photo availabel for individual
    _ = PhotoIdentificationTaskResultFactory(type=BaseTaskResult.ResultType.ENSEMBLED, task=photo_task1)
    _ = PhotoIdentificationTaskResultFactory(type=BaseTaskResult.ResultType.ENSEMBLED, task=photo_task2)

    assert list(report.individuals.all()) == [individual]

    photo_task1.delete()

    assert list(report.individuals.all()) == [individual]

    photo_task2.delete()

    assert not report.individuals.exists()
