from contextlib import nullcontext as does_not_raise
from datetime import timedelta
from decimal import Decimal
import math
import pytest
from scipy.stats import entropy
import time_machine
from unittest.mock import PropertyMock, patch, MagicMock
import uuid


from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.db import IntegrityError
from django.utils import timezone
from django.utils.translation import gettext as _

from mosquito_alert.geo.tests.factories import EuropeCountryFactory, NutsEuropeFactory
from mosquito_alert.taxa.models import Taxon
from mosquito_alert.identification_tasks.models import (
    ExpertReportAnnotation,
    IdentificationTask,
)
from mosquito_alert.notifications.models import Notification
from mosquito_alert.reports.models import Report, Photo
from mosquito_alert.users.tests.factories import UserFactory
from mosquito_alert.workspaces.models import Workspace, WorkspaceMembership
from mosquito_alert.workspaces.tests.factories import (
    WorkspaceFactory,
    WorkspaceCollaborationGroupFactory,
)

from .factories import IdentificationTaskFactory, ExpertReportAnnotationFactory


@pytest.mark.django_db
class TestExpertReportAnnotationModel:
    def test_taxon_field_can_be_null(self):
        assert ExpertReportAnnotation._meta.get_field("taxon").null

    def test_confidence_field_cannot_be_null(self):
        assert not ExpertReportAnnotation._meta.get_field("confidence").null

    @pytest.mark.parametrize(
        "value, expected_raise",
        [
            (0, does_not_raise()),
            (1, does_not_raise()),
            (0.5, does_not_raise()),
            (-0.1, pytest.raises(IntegrityError)),
            (1.1, pytest.raises(IntegrityError)),
        ],
    )
    def test_confidence_raise_if_not_between_0_and_1(
        self, user, identification_task, value, expected_raise
    ):
        obj = ExpertReportAnnotation.objects.create(
            user=user, identification_task=identification_task
        )

        # Need to force update, because save() sets the confidence automatically
        with expected_raise:
            ExpertReportAnnotation.objects.filter(pk=obj.pk).update(confidence=value)

    # properties
    @pytest.mark.parametrize(
        "confidence_value, expected_result",
        [
            (0, _("Not sure")),
            (0.49, _("Not sure")),
            (0.5, _("species_value_possible")),
            (0.75, _("species_value_possible")),
            (0.89, _("species_value_possible")),
            (0.9, _("species_value_confirmed")),
            (1, _("species_value_confirmed")),
        ],
    )
    def test_confidence_label(self, confidence_value, expected_result):
        obj = ExpertReportAnnotation(confidence=confidence_value)
        assert obj.confidence_label == expected_result

    def test_userstat_grabbed_reports_is_incremented_on_create(
        self, user, identification_task
    ):
        userstat = user.userstat
        assert userstat.grabbed_reports == 0

        _ = ExpertReportAnnotation.objects.create(
            user=user, identification_task=identification_task
        )

        userstat.refresh_from_db()

        assert userstat.grabbed_reports == 1

    def test_identification_task_is_called_to_refresh_on_create(
        self, user, identification_task
    ):
        with patch.object(IdentificationTask, "refresh") as mocked_refresh:
            _ = ExpertReportAnnotation.objects.create(
                user=user, identification_task=identification_task
            )

            # Check if refresh() was called
            mocked_refresh.assert_called_once()

    def test_identification_task_is_called_to_refresh_on_save(
        self, user, identification_task
    ):
        obj = ExpertReportAnnotation.objects.create(
            user=user, identification_task=identification_task
        )

        with patch.object(obj.identification_task, "refresh") as mocked_refresh:
            obj.save()

            mocked_refresh.assert_called_once()

    def test_identification_task_is_called_to_refresh_on_delete(
        self, user, identification_task
    ):
        obj = ExpertReportAnnotation.objects.create(
            user=user, identification_task=identification_task
        )

        with patch.object(obj.identification_task, "refresh") as mocked_refresh:
            obj.delete()

            mocked_refresh.assert_called_once()

    def test_confidence_set_to_0_if_not_taxon(self, user, identification_task):
        obj = ExpertReportAnnotation.objects.create(
            user=user,
            identification_task=identification_task,
            taxon=None,
            confidence=0.5,
        )

        obj.refresh_from_db()

        assert obj.confidence == 0

    @pytest.mark.parametrize("num_annotations", [0, 1, 2, 3])
    def test_is_simplified_False_if_decision_level_FINAL(
        self, identification_task, num_annotations
    ):
        ExpertReportAnnotationFactory.create_batch(
            size=num_annotations,
            identification_task=identification_task,
            is_finished=False,
        )

        obj = ExpertReportAnnotationFactory(
            identification_task=identification_task,
            decision_level=ExpertReportAnnotation.DecisionLevel.FINAL,
            is_finished=False,
        )
        assert not obj.is_simplified

    @pytest.mark.parametrize("num_annotations", [0, 1, 2, 3])
    def test_is_simplified_False_if_country_supervisor(
        self, user_national_supervisor, identification_task, num_annotations
    ):
        ExpertReportAnnotationFactory.create_batch(
            size=num_annotations,
            identification_task=identification_task,
            is_finished=False,
        )

        obj = ExpertReportAnnotationFactory(
            identification_task=identification_task,
            user=user_national_supervisor,
            is_finished=False,
        )
        assert not obj.is_simplified

    @pytest.mark.parametrize(
        "num_annotations, expected_is_simplified", [(0, True), (1, True), (2, False)]
    )
    def test_is_simplified(
        self, identification_task, num_annotations, expected_is_simplified
    ):
        ExpertReportAnnotationFactory.create_batch(
            size=num_annotations,
            identification_task=identification_task,
            is_finished=False,
        )

        obj = ExpertReportAnnotationFactory(
            identification_task=identification_task, is_finished=False
        )
        assert obj.is_simplified == expected_is_simplified


@pytest.mark.django_db
class TestIdentificationTaskModel:
    # classmethods
    @pytest.mark.parametrize("report_type", [Report.TYPE_BITE, Report.TYPE_SITE])
    def test_get_or_create_for_report_should_return_None_if_not_adult_report(
        self, _report, report_type
    ):
        report = _report
        report.type = report_type
        report.save()

        result, created = IdentificationTask.get_or_create_for_report(report=report)
        assert result is None
        assert not created

    def test_get_or_create_for_report_should_return_None_if_report_has_no_photos(
        self, adult_report
    ):
        assert frozenset(adult_report.photos.all()) is frozenset([])

        result, created = IdentificationTask.get_or_create_for_report(
            report=adult_report
        )
        assert result is None
        assert not created

    def test_get_or_create_for_report_in_supervised_country_should_return_task_with_exclusivity_end_date(
        self, user_national_supervisor, country, adult_report
    ):
        assert adult_report.country == country

        # Creating a photo will auto create a new IdentificationTask. Delete it and force manual.
        _ = Photo.objects.create(report=adult_report, photo="./testdata/splash.png")
        IdentificationTask.objects.filter(report=adult_report).delete()

        obj, created = IdentificationTask.get_or_create_for_report(report=adult_report)

        assert obj is not None
        assert created
        assert obj.exclusivity_end == adult_report.server_upload_time + timedelta(
            days=10
        )

    def test_get_taxon_consensus_empty_annotations(self):
        result = IdentificationTask.get_taxon_consensus([], min_confidence=0.5)
        assert result == (None, 0.0, 1.0, 0.0)

    def test_get_taxon_consensus_no_taxon(self):
        """Test when annotations have no taxon."""
        annotations = [
            MagicMock(spec=ExpertReportAnnotation, taxon=None, confidence=0.7),
            MagicMock(spec=ExpertReportAnnotation, taxon=None, confidence=0.5),
        ]
        result = IdentificationTask.get_taxon_consensus(annotations, min_confidence=0.5)
        assert result == (None, 1.0, 0.0, 1.0)

    def test_get_taxon_consensus_below_confidence_threshold(self, taxon_root):
        """Test when the annotations have taxons, but no taxon meets the minimum confidence threshold."""
        annotations = [
            MagicMock(spec=ExpertReportAnnotation, taxon=taxon_root, confidence=0.3),
            MagicMock(spec=ExpertReportAnnotation, taxon=taxon_root, confidence=0.2),
        ]
        result = IdentificationTask.get_taxon_consensus(annotations, min_confidence=0.5)
        assert result == (None, 0.0, 1.0, 0.0)

    def test_get_taxon_consensus_valid_annotations(self, taxon_root):
        """Test when valid annotations exist and meet the confidence threshold."""
        genus = taxon_root.add_child(name="genus", rank=Taxon.TaxonomicRank.GENUS)
        specie_1 = genus.add_child(name="specie 1", rank=Taxon.TaxonomicRank.SPECIES)
        _ = genus.add_child(name="specie 2", rank=Taxon.TaxonomicRank.SPECIES)

        annotations = [
            MagicMock(spec=ExpertReportAnnotation, taxon=specie_1, confidence=0.75),
            MagicMock(spec=ExpertReportAnnotation, taxon=specie_1, confidence=1),
        ]

        result = IdentificationTask.get_taxon_consensus(annotations, min_confidence=0.5)
        assert result[0] == specie_1
        assert result[1] == 0.875
        assert result[2] == entropy([0.875, 0.125], base=2) / math.log2(2)
        assert result[3] == 1

    # fields
    def test_report_field_is_primary_key(self):
        assert IdentificationTask._meta.get_field("report").primary_key

    def test_status_is_db_index(self):
        assert IdentificationTask._meta.get_field("status").db_index

    def test_status_is_set_to_OPEN_as_default(self):
        assert (
            IdentificationTask._meta.get_field("status").default
            == IdentificationTask.Status.OPEN
        )

    def test_is_flagged_is_False_default(self):
        assert not IdentificationTask._meta.get_field("is_flagged").default

    def test_is_safe_is_False_default(self):
        assert not IdentificationTask._meta.get_field("is_safe").default

    def test_public_note_is_nullable(self):
        assert IdentificationTask._meta.get_field("public_note").null

    def test_message_for_user_is_nullable(self):
        assert IdentificationTask._meta.get_field("message_for_user").null

    def test_total_annotations_is_0_default(self):
        assert IdentificationTask._meta.get_field("total_annotations").default == 0

    def test_total_finished_annotations_is_0_default(self):
        assert (
            IdentificationTask._meta.get_field("total_finished_annotations").default
            == 0
        )

    def test_review_type_is_nullable(self):
        assert IdentificationTask._meta.get_field("review_type").null

    def test_review_type_is_None_default(self):
        assert IdentificationTask._meta.get_field("review_type").default is None

    def test_reviewed_at_is_nullable(self):
        assert IdentificationTask._meta.get_field("reviewed_at").null

    def test_reviewed_by_is_nullable(self):
        assert IdentificationTask._meta.get_field("reviewed_by").null

    def test_taxon_is_nullable(self):
        assert IdentificationTask._meta.get_field("taxon").null

    def test_confidence_is_decimal_0_default(self):
        assert IdentificationTask._meta.get_field("confidence").default == Decimal("0")

    def test_uncertainty_is_float_1_default(self):
        assert IdentificationTask._meta.get_field("uncertainty").default == 1.0

    def test_agreement_is_float_0_default(self):
        assert IdentificationTask._meta.get_field("agreement").default == 0.0

    def test_created_at_is_auto_now_add(self):
        assert IdentificationTask._meta.get_field("created_at").auto_now_add

    def test_updated_at_is_auto_now(self):
        assert IdentificationTask._meta.get_field("updated_at").auto_now

    # properties
    def test_exclusivity_end(
        self, identification_task, country, user_national_supervisor
    ):
        assert identification_task.report.country == country

        workspace = Workspace.objects.get(country=country)
        assert (
            identification_task.exclusivity_end
            == identification_task.report.server_upload_time
            + timedelta(days=workspace.supervisor_exclusivity_days)
        )

        # Delete the national supervisor.
        user_national_supervisor.delete()
        # clear cached for exclusivity_end @cached_property, requiring re-computation next time it's called
        del identification_task.exclusivity_end
        assert identification_task.exclusivity_end is None

    def test_in_exclusivity_period(self):
        with time_machine.travel("2024-01-01 00:00:00", tick=False) as traveller:
            obj = IdentificationTask()

            with patch.object(
                IdentificationTask, "exclusivity_end", new_callable=PropertyMock
            ) as mock_property:
                mock_property.return_value = timezone.now() + timedelta(
                    days=1
                )  # Set mock return value

                assert obj.in_exclusivity_period

                traveller.shift(timedelta(days=1))

                assert not obj.in_exclusivity_period

    @pytest.mark.parametrize(
        "value, expected_result",
        [
            (IdentificationTask.Status.OPEN, False),
            (IdentificationTask.Status.CONFLICT, False),
            (IdentificationTask.Status.REVIEW, False),
            (IdentificationTask.Status.ARCHIVED, False),
            (IdentificationTask.Status.DONE, True),
        ],
    )
    def test_is_done(self, value, expected_result):
        obj = IdentificationTask(status=value)
        assert obj.is_done == expected_result

    @pytest.mark.parametrize(
        "reviewed_datetime, expected_result",
        [
            (timezone.now(), True),
            (None, False),
        ],
    )
    def test_is_reviewed(self, reviewed_datetime, expected_result):
        obj = IdentificationTask(reviewed_at=reviewed_datetime)
        assert obj.is_reviewed == expected_result

    # methods
    def test_assign_to_user_creates_expert_report_annotation(
        self, user, identification_task
    ):
        annotations_qs = ExpertReportAnnotation.objects.filter(
            identification_task=identification_task
        )
        assert annotations_qs.count() == 0

        identification_task.assign_to_user(user=user)

        assert annotations_qs.count() == 1

        annotation = annotations_qs.get(user=user)
        assert not annotation.is_finished

    # constraints
    @pytest.mark.parametrize(
        "total_annotations, total_finished_annotations, expected_raise",
        [
            (0, 0, does_not_raise()),
            (1, 1, does_not_raise()),
            (2, 1, does_not_raise()),
            (0, 1, pytest.raises(IntegrityError)),
            (1, 2, pytest.raises(IntegrityError)),
        ],
    )
    def test_total_finished_annotations_must_be_lte_total_annotations(
        self,
        identification_task,
        total_annotations,
        total_finished_annotations,
        expected_raise,
    ):
        with expected_raise:
            identification_task.total_annotations = total_annotations
            identification_task.total_finished_annotations = total_finished_annotations
            identification_task.save()

    @pytest.mark.parametrize(
        "value, expected_raise",
        [
            (Decimal("0"), does_not_raise()),
            (Decimal("0.5"), does_not_raise()),
            (Decimal("1"), does_not_raise()),
            (Decimal("-0.1"), pytest.raises(IntegrityError)),
            (Decimal("1.1"), pytest.raises(IntegrityError)),
        ],
    )
    def test_confidence_between_decimal0_decimal1(
        self, identification_task, value, expected_raise
    ):
        with expected_raise:
            identification_task.confidence = value
            identification_task.save()

    @pytest.mark.parametrize(
        "value, expected_raise",
        [
            (0, does_not_raise()),
            (0.5, does_not_raise()),
            (1, does_not_raise()),
            (-0.1, pytest.raises(IntegrityError)),
            (1.1, pytest.raises(IntegrityError)),
        ],
    )
    def test_uncertainty_between_float0_float1(
        self, identification_task, value, expected_raise
    ):
        with expected_raise:
            identification_task.uncertainty = value
            identification_task.save()

    @pytest.mark.parametrize(
        "value, expected_raise",
        [
            (0, does_not_raise()),
            (0.5, does_not_raise()),
            (1, does_not_raise()),
            (-0.1, pytest.raises(IntegrityError)),
            (1.1, pytest.raises(IntegrityError)),
        ],
    )
    def test_agreement_between_float0_float1(
        self, identification_task, value, expected_raise
    ):
        with expected_raise:
            identification_task.agreement = value
            identification_task.save()


@pytest.mark.django_db
class TestIdentificationTaskManager:
    """Test IdentificationTaskQuerySet methods."""

    # Test new() method
    def test_new_returns_never_assigned_tasks(self, identification_task):
        """new() should return tasks with status=OPEN and total_annotations=0."""
        assert identification_task.status == IdentificationTask.Status.OPEN
        assert identification_task.total_annotations == 0

        result = IdentificationTask.objects.new()

        assert result.count() == 1
        assert result.first() == identification_task

    def test_new_excludes_tasks_with_annotations(self, identification_task, user):
        """new() should exclude tasks that have annotations."""
        identification_task.assign_to_user(user=user)
        identification_task.refresh_from_db()

        assert identification_task.total_annotations == 1

        result = IdentificationTask.objects.new()

        assert result.count() == 0

    def test_new_excludes_non_open_tasks(self, identification_task):
        """new() should exclude tasks that are not OPEN."""
        identification_task.status = IdentificationTask.Status.DONE
        identification_task.save()

        result = IdentificationTask.objects.new()

        assert result.count() == 0

    # Test ongoing() method
    def test_ongoing_returns_tasks_with_annotations(self, identification_task, user):
        """ongoing() should return tasks with total_annotations > 0."""
        identification_task.assign_to_user(user=user)
        identification_task.refresh_from_db()

        result = IdentificationTask.objects.ongoing()

        assert result.count() == 1
        assert result.first() == identification_task

    def test_ongoing_excludes_new_tasks(self, identification_task):
        """ongoing() should exclude tasks with no annotations."""
        result = IdentificationTask.objects.ongoing()

        assert result.count() == 0

    def test_ongoing_excludes_non_open_tasks(self, identification_task, user):
        """ongoing() should exclude tasks that are not OPEN."""
        identification_task.assign_to_user(user=user)
        identification_task.status = IdentificationTask.Status.DONE
        identification_task.save()

        result = IdentificationTask.objects.ongoing()

        assert result.count() == 0

    # Test annotating() method
    def test_annotating_returns_tasks_being_labeled(self, identification_task, user):
        """annotating() should return tasks with unfinished annotations."""
        identification_task.assign_to_user(user=user)

        result = IdentificationTask.objects.annotating()

        assert result.count() == 1
        assert result.first() == identification_task

    def test_annotating_excludes_completed_tasks(self, identification_task, user):
        """annotating() should exclude tasks where all annotations are finished."""
        ExpertReportAnnotationFactory(
            identification_task=identification_task, user=user, is_finished=True
        )

        result = IdentificationTask.objects.annotating()

        assert result.count() == 0

    # Test to_review() method
    @pytest.mark.parametrize(
        "status", [IdentificationTask.Status.CONFLICT, IdentificationTask.Status.REVIEW]
    )
    def test_to_review_returns_conflict_or_review_status(
        self, identification_task, status: IdentificationTask.Status
    ):
        """to_review() should return tasks with CONFLICT or REVIEW status."""
        identification_task.status = status
        identification_task.save()

        result = IdentificationTask.objects.to_review()

        assert result.count() == 1
        assert result.first() == identification_task

    def test_to_review_returns_done_without_review(self, identification_task):
        """to_review() should return DONE tasks without reviewed_at."""
        identification_task.status = IdentificationTask.Status.DONE
        identification_task.reviewed_at = None
        identification_task.save()

        result = IdentificationTask.objects.to_review()

        assert result.count() == 1

    def test_to_review_excludes_done_with_review(self, identification_task, user):
        """to_review() should exclude DONE tasks with reviewed_at set."""
        identification_task.status = IdentificationTask.Status.DONE
        identification_task.reviewed_at = timezone.now()
        identification_task.reviewed_by = user
        identification_task.save()

        result = IdentificationTask.objects.to_review()

        assert result.count() == 0

    # Test closed() method
    def test_closed_returns_done_status(self, identification_task):
        """closed() should return tasks with DONE status."""
        identification_task.status = IdentificationTask.Status.DONE
        identification_task.save()

        result = IdentificationTask.objects.closed()

        assert result.count() == 1

    def test_closed_returns_archived_status(self, identification_task):
        """closed() should return tasks with ARCHIVED status."""
        identification_task.status = IdentificationTask.Status.ARCHIVED
        identification_task.save()

        result = IdentificationTask.objects.closed()

        assert result.count() == 1

    def test_closed_excludes_open_status(self, identification_task):
        """closed() should exclude OPEN tasks."""
        result = IdentificationTask.objects.closed()

        assert result.count() == 0

    # Test done() method
    def test_done_returns_done_status_by_default(self, identification_task):
        """done() should return tasks with DONE status."""
        identification_task.status = IdentificationTask.Status.DONE
        identification_task.save()

        result = IdentificationTask.objects.done()

        assert result.count() == 1

    def test_done_with_false_excludes_done_status(self, identification_task):
        """done(state=False) should exclude DONE tasks."""
        identification_task.status = IdentificationTask.Status.DONE
        identification_task.save()

        result = IdentificationTask.objects.done(state=False)

        assert result.count() == 0

    def test_done_excludes_archived(self, identification_task):
        """done() should exclude ARCHIVED tasks."""
        identification_task.status = IdentificationTask.Status.ARCHIVED
        identification_task.save()

        result = IdentificationTask.objects.done()

        assert result.count() == 0

    # Test blocked() method
    def test_blocked_returns_tasks_with_stale_annotations(
        self, identification_task, user
    ):
        """blocked() should return ongoing tasks with stale annotations."""
        with time_machine.travel("2024-01-01 00:00:00", tick=False) as traveller:
            ExpertReportAnnotationFactory(
                identification_task=identification_task, user=user, is_finished=False
            )

            traveller.shift(timedelta(days=settings.ENTOLAB_LOCK_PERIOD + 1))

            result = IdentificationTask.objects.blocked()

            assert result.count() == 1
            assert result.first() == identification_task

    def test_blocked_excludes_recent_annotations(self, identification_task, user):
        """blocked() should exclude tasks with recent annotations."""
        with time_machine.travel("2024-01-01 00:00:00", tick=False) as traveller:
            ExpertReportAnnotationFactory(
                identification_task=identification_task,
                user=user,
                is_finished=False,
            )

            traveller.shift(timedelta(days=settings.ENTOLAB_LOCK_PERIOD - 1))

            result = IdentificationTask.objects.blocked()

            assert result.count() == 0

    def test_blocked_respects_custom_days(self, identification_task, user):
        """blocked(days) should respect custom days parameter."""
        with time_machine.travel("2024-01-01 00:00:00", tick=False) as traveller:
            ExpertReportAnnotationFactory(
                identification_task=identification_task,
                user=user,
                is_finished=False,
            )

            traveller.shift(timedelta(days=5))

            result = IdentificationTask.objects.blocked(days=3)

            assert result.count() == 1

    # Test in_exclusivity_period() method
    @time_machine.travel("2024-01-01 00:00:00", tick=False)
    def test_in_exclusivity_period_returns_tasks_in_period(
        self, identification_task, user_national_supervisor, country
    ):
        """in_exclusivity_period() should return tasks within exclusivity period."""
        workspace = Workspace.objects.get(country=country)
        identification_task.report.server_upload_time = timezone.now() - timedelta(
            days=workspace.supervisor_exclusivity_days - 1
        )
        identification_task.report.save()

        result = IdentificationTask.objects.in_exclusivity_period()

        assert result.count() == 1

    @time_machine.travel("2024-01-01 00:00:00", tick=False)
    def test_in_exclusivity_period_excludes_expired_tasks(
        self, identification_task, user_national_supervisor, country
    ):
        """in_exclusivity_period() should exclude tasks past exclusivity."""
        workspace = Workspace.objects.get(country=country)
        identification_task.report.server_upload_time = timezone.now() - timedelta(
            days=workspace.supervisor_exclusivity_days + 1
        )
        identification_task.report.save()

        result = IdentificationTask.objects.in_exclusivity_period()

        assert result.count() == 0

    @time_machine.travel("2024-01-01 00:00:00", tick=False)
    def test_in_exclusivity_period_excludes_if_supervisor_annotated(
        self, identification_task, user_national_supervisor, country
    ):
        """in_exclusivity_period() should exclude tasks where supervisor annotated."""
        workspace = Workspace.objects.get(country=country)
        identification_task.report.server_upload_time = timezone.now() - timedelta(
            days=workspace.supervisor_exclusivity_days - 1
        )
        identification_task.report.save()

        ExpertReportAnnotationFactory(
            identification_task=identification_task,
            user=user_national_supervisor,
            is_finished=True,
        )

        result = IdentificationTask.objects.in_exclusivity_period()

        assert result.count() == 0

    def test_in_exclusivity_period_excludes_without_supervisor(
        self, identification_task, country
    ):
        """in_exclusivity_period() should exclude tasks in countries without supervisor."""
        result = IdentificationTask.objects.in_exclusivity_period()

        # Country has no supervisor after removing from fixture
        assert result.count() == 0

    @time_machine.travel("2024-01-01 00:00:00", tick=False)
    def test_in_exclusivity_period_with_false_state(
        self, identification_task, user_national_supervisor, country
    ):
        """in_exclusivity_period(state=False) should return tasks NOT in exclusivity."""
        workspace = Workspace.objects.get(country=country)
        identification_task.report.server_upload_time = timezone.now() - timedelta(
            days=workspace.supervisor_exclusivity_days + 1
        )
        identification_task.report.save()

        result = IdentificationTask.objects.in_exclusivity_period(state=False)

        assert result.count() == 1

    # Test supervisor_has_annotated() method
    def test_supervisor_has_annotated_returns_tasks(
        self, identification_task, user_national_supervisor, country
    ):
        """supervisor_has_annotated() should return tasks where supervisor annotated."""
        ExpertReportAnnotationFactory(
            identification_task=identification_task,
            user=user_national_supervisor,
            is_finished=True,
        )

        result = IdentificationTask.objects.supervisor_has_annotated()

        assert result.count() == 1

    def test_supervisor_has_annotated_excludes_unfinished(
        self, identification_task, user_national_supervisor, country
    ):
        """supervisor_has_annotated() should exclude tasks with unfinished supervisor annotations."""
        identification_task.assign_to_user(user=user_national_supervisor)

        result = IdentificationTask.objects.supervisor_has_annotated()

        assert result.count() == 0

    def test_supervisor_has_annotated_excludes_regular_users(
        self, identification_task, user
    ):
        """supervisor_has_annotated() should exclude tasks annotated by non-supervisors."""
        ExpertReportAnnotationFactory(
            identification_task=identification_task, user=user, is_finished=True
        )

        result = IdentificationTask.objects.supervisor_has_annotated()

        assert result.count() == 0

    def test_supervisor_has_annotated_with_false_state(
        self, identification_task, user_national_supervisor
    ):
        """supervisor_has_annotated(state=False) should return tasks where supervisor has NOT annotated."""
        result = IdentificationTask.objects.supervisor_has_annotated(state=False)

        assert result.count() == 1

    # Test annotated_by() method
    def test_annotated_by_returns_user_tasks(self, identification_task, user):
        """annotated_by() should return tasks annotated by specified users."""
        ExpertReportAnnotationFactory(
            identification_task=identification_task, user=user, is_finished=True
        )

        result = IdentificationTask.objects.annotated_by(users=[user])

        assert result.count() == 1

    def test_annotated_by_excludes_unfinished(self, identification_task, user):
        """annotated_by() should exclude tasks with unfinished annotations."""
        identification_task.assign_to_user(user=user)

        result = IdentificationTask.objects.annotated_by(users=[user])

        assert result.count() == 0

    def test_annotated_by_excludes_other_users(self, identification_task):
        """annotated_by() should exclude tasks not annotated by specified users."""
        other_user = UserFactory()

        result = IdentificationTask.objects.annotated_by(users=[other_user])

        assert result.count() == 0

    def test_annotated_by_multiple_users(self, identification_task, user):
        """annotated_by() should work with multiple users."""
        user2 = UserFactory()

        ExpertReportAnnotationFactory(
            identification_task=identification_task, user=user, is_finished=True
        )

        result = IdentificationTask.objects.annotated_by(users=[user, user2])

        assert result.count() == 1

    # Test assigned_to() method
    def test_assigned_to_returns_user_tasks(self, identification_task, user):
        """assigned_to() should return tasks assigned to specified users."""
        identification_task.assign_to_user(user=user)

        result = IdentificationTask.objects.assigned_to(users=[user])

        assert result.count() == 1

    def test_assigned_to_includes_unfinished(self, identification_task, user):
        """assigned_to() should include tasks with unfinished annotations."""
        identification_task.assign_to_user(user=user)

        result = IdentificationTask.objects.assigned_to(users=[user])

        assert result.count() == 1

    def test_assigned_to_excludes_other_users(self, identification_task):
        """assigned_to() should exclude tasks not assigned to specified users."""
        other_user = UserFactory()

        result = IdentificationTask.objects.assigned_to(users=[other_user])

        assert result.count() == 0

    # Test backlog() method
    def test_backlog_without_user_returns_assignable_tasks(self, identification_task):
        """backlog() without user should return all assignable tasks."""
        result = IdentificationTask.objects.backlog(user=None)

        assert result.count() == 1

    def test_backlog_excludes_assigned_to_user(
        self, identification_task, user, country
    ):
        """backlog(user) should exclude tasks already assigned to user."""
        # Create workspace membership for user
        WorkspaceMembership.objects.create(
            workspace=WorkspaceFactory(country=country),
            user=user,
            role=WorkspaceMembership.Role.ANNOTATOR,
        )

        identification_task.assign_to_user(user=user)

        result = IdentificationTask.objects.backlog(user=user)

        assert result.count() == 0

    def test_backlog_excludes_max_assigned_tasks(self, identification_task):
        """backlog() should exclude tasks with maximum annotations."""
        for i in range(settings.MAX_N_OF_EXPERTS_ASSIGNED_PER_REPORT):
            user = UserFactory()
            identification_task.assign_to_user(user=user)

        result = IdentificationTask.objects.backlog(user=None)

        assert result.count() == 0

    def test_backlog_user_without_workspace_role_returns_nothing(
        self, identification_task, user
    ):
        """backlog() should return nothing for users without workspace memberships."""
        WorkspaceMembership.objects.create(
            workspace=WorkspaceFactory(country=identification_task.report.country),
            user=user,
            role=WorkspaceMembership.Role.MEMBER,
        )

        result = IdentificationTask.objects.backlog(user=user)

        assert result.count() == 0

    def test_backlog_prioritizes_user_workspace(self, country, user):
        """backlog() should prioritize tasks from user's workspace."""
        # Create workspace membership
        WorkspaceMembership.objects.create(
            workspace=WorkspaceFactory(country=country),
            user=user,
            role=WorkspaceMembership.Role.ANNOTATOR,
        )

        identification_task = IdentificationTaskFactory(
            report__point=country.geom.point_on_surface
        )

        IdentificationTaskFactory()

        result = IdentificationTask.objects.backlog(user=user)

        assert result.count() == 2
        assert result.first() == identification_task

    def test_backlog_orders_by_upload_time_recent_first(self, country, user):
        """backlog() should order tasks by report upload time (newest first)."""
        WorkspaceMembership.objects.create(
            workspace=WorkspaceFactory(country=country),
            user=user,
            role=WorkspaceMembership.Role.ANNOTATOR,
        )

        with time_machine.travel("2024-01-01 00:00:00", tick=False) as traveller:
            old_identification_task = IdentificationTaskFactory(
                report__point=country.geom.point_on_surface,
            )

            traveller.shift(timedelta(days=1))

            new_identification_task = IdentificationTaskFactory(
                report__point=country.geom.point_on_surface,
            )

        result = IdentificationTask.objects.backlog(user=user)

        assert list(result) == [new_identification_task, old_identification_task]

    def test_backlog_supervisor_sees_exclusivity_tasks(
        self, country, user_national_supervisor
    ):
        """backlog() should show tasks in exclusivity period to supervisors."""

        identification_task = IdentificationTaskFactory(
            report__point=country.geom.point_on_surface
        )

        result = IdentificationTask.objects.backlog(user=user_national_supervisor)

        assert result.count() == 1
        assert result.first() == identification_task

    def test_backlog_annotator_doesnt_see_exclusivity_tasks(
        self, country, user_national_supervisor
    ):
        """backlog() should not show tasks in exclusivity period to regular annotators."""
        annotator_user = UserFactory()

        WorkspaceMembership.objects.create(
            workspace=country.workspace,
            user=annotator_user,
            role=WorkspaceMembership.Role.ANNOTATOR,
        )

        IdentificationTaskFactory(report__point=country.geom.point_on_surface)
        result = IdentificationTask.objects.backlog(user=annotator_user)

        assert result.count() == 0

    def test_backlog_annotator_can_see_exclusivity_tasks_after_period(
        self, country, user_national_supervisor
    ):
        """backlog() should show tasks in exclusivity period to regular annotators after exclusivity ends."""
        annotator_user = UserFactory()

        WorkspaceMembership.objects.create(
            workspace=country.workspace,
            user=annotator_user,
            role=WorkspaceMembership.Role.ANNOTATOR,
        )

        with time_machine.travel("2024-01-01 00:00:00", tick=False) as traveller:
            identification_task = IdentificationTaskFactory(
                report__point=country.geom.point_on_surface
            )

            traveller.shift(
                timedelta(days=country.workspace.supervisor_exclusivity_days + 1)
            )

            result = IdentificationTask.objects.backlog(user=annotator_user)

            assert result.count() == 1
            assert result.first() == identification_task

    def test_backlog_annotator_can_see_exclusitivty_tasks_after_supervisor_annotation(
        self, country, user_national_supervisor
    ):
        """backlog() should show tasks in exclusivity period to regular annotators after supervisor annotation."""
        annotator_user = UserFactory()

        WorkspaceMembership.objects.create(
            workspace=country.workspace,
            user=annotator_user,
            role=WorkspaceMembership.Role.ANNOTATOR,
        )

        identification_task = IdentificationTaskFactory(
            report__point=country.geom.point_on_surface
        )

        ExpertReportAnnotationFactory(
            identification_task=identification_task,
            user=user_national_supervisor,
            is_finished=True,
        )

        result = IdentificationTask.objects.backlog(user=annotator_user)

        assert result.count() == 1
        assert result.first() == identification_task

    def test_backlog_user_sees_from_unkown_countries(self, user, country):
        """backlog() should return tasks from unknown countries for users without workspace memberships."""
        WorkspaceMembership.objects.create(
            workspace=WorkspaceFactory(country=country),
            user=user,
            role=WorkspaceMembership.Role.ANNOTATOR,
        )

        identification_task = IdentificationTaskFactory(
            report__point=Point(0, 0)  # Point in international waters
        )

        result = IdentificationTask.objects.backlog(user=user)

        assert result.count() == 1
        assert result.first() == identification_task

    @pytest.mark.parametrize("collaboration_exists", [False, True])
    def test_backlog_user_only_sees_other_workspace_if_collaboration_agreement(
        self, collaboration_exists: bool
    ):
        """backlog() should not return tasks from other workspaces unless collaboration agreement exists."""
        user = UserFactory()

        user_workspace = WorkspaceFactory()
        WorkspaceMembership.objects.create(
            workspace=user_workspace, user=user, role=WorkspaceMembership.Role.ANNOTATOR
        )

        other_workspace = WorkspaceFactory()

        IdentificationTaskFactory(
            report__point=other_workspace.country.geom.point_on_surface
        )

        if collaboration_exists:
            WorkspaceCollaborationGroupFactory(
                workspaces=[user_workspace, other_workspace]
            )

        result = IdentificationTask.objects.backlog(user=user)

        assert result.exists() == collaboration_exists

    def test_backlog_user_prioritizes_nuts2(self):
        """backlog() should prioritize tasks from user's NUTS2 region."""
        user = UserFactory()

        workspace = WorkspaceFactory()
        WorkspaceMembership.objects.create(
            workspace=workspace, user=user, role=WorkspaceMembership.Role.ANNOTATOR
        )

        nuts2_region = NutsEuropeFactory(
            levl_code=2, europecountry=workspace.country, geom=workspace.country.geom
        )

        user.userstat.nuts2_assignation = nuts2_region
        user.userstat.save()

        task_in_nuts2 = IdentificationTaskFactory(
            report__point=nuts2_region.geom.point_on_surface
        )

        task_outside_nuts2 = IdentificationTaskFactory()

        result = IdentificationTask.objects.backlog(user=user)

        assert result.count() == 2
        assert list(result) == [task_in_nuts2, task_outside_nuts2]

    def test_backlog_prioritizes_countries_without_workspace(self):
        """backlog() should include tasks from countries without workspace (priority 1)."""
        user = UserFactory()

        user_workspace = WorkspaceFactory()
        WorkspaceMembership.objects.create(
            workspace=user_workspace, user=user, role=WorkspaceMembership.Role.ANNOTATOR
        )

        # Create a country without a workspace
        country_without_workspace = EuropeCountryFactory()

        task_no_workspace = IdentificationTaskFactory(
            report__point=country_without_workspace.geom.point_on_surface,
            report__country=country_without_workspace,
        )

        result = IdentificationTask.objects.backlog(user=user)

        assert result.filter(pk=task_no_workspace.pk).exists()

    def test_backlog_combined_priority_ordering(self):
        """backlog() should correctly order tasks across all priority levels."""
        user = UserFactory()

        # Setup: user workspace (priority 3)
        user_workspace = WorkspaceFactory()
        WorkspaceMembership.objects.create(
            workspace=user_workspace, user=user, role=WorkspaceMembership.Role.ANNOTATOR
        )

        # Setup: NUTS2 region (priority 4 - highest)
        nuts2_region = NutsEuropeFactory(
            levl_code=2,
            europecountry=user_workspace.country,
            geom=user_workspace.country.geom,
        )
        user.userstat.nuts2_assignation = nuts2_region
        user.userstat.save()

        # Setup: collaboration group (priority 2)
        collab_workspace = WorkspaceFactory()
        WorkspaceCollaborationGroupFactory(
            workspaces=[user_workspace, collab_workspace]
        )

        # Setup: country without workspace (priority 1)
        country_no_workspace = EuropeCountryFactory()

        # Setup: unknown country (prioritized)
        # Create tasks in all categories
        task_nuts2 = IdentificationTaskFactory(
            report__point=nuts2_region.geom.point_on_surface,
            report__country=user_workspace.country,
        )

        IdentificationTaskFactory(
            report__point=user_workspace.country.geom.point_on_surface,
            report__country=user_workspace.country,
        )

        task_collab = IdentificationTaskFactory(
            report__point=collab_workspace.country.geom.point_on_surface,
            report__country=collab_workspace.country,
        )

        task_no_workspace = IdentificationTaskFactory(
            report__point=country_no_workspace.geom.point_on_surface,
            report__country=country_no_workspace,
        )

        task_unknown = IdentificationTaskFactory(
            report__point=Point(0, 0),  # International waters
            report__country=None,
        )

        result = list(IdentificationTask.objects.backlog(user=user))

        # Expected order: unknown country, NUTS2 (4), user workspace (3), collaboration (2), no workspace (1)
        # Since unknown country gets filtered first, then ordered by priority
        assert task_nuts2 in result[:2]  # NUTS2 should be in top results
        assert task_unknown in result  # Unknown country should be included
        assert result.index(task_nuts2) < result.index(
            task_collab
        )  # NUTS2 before collab
        assert result.index(task_collab) < result.index(
            task_no_workspace
        )  # collab before no workspace

    def test_backlog_supervisor_exclusivity_tasks_ordered_first(
        self, country, user_national_supervisor
    ):
        """backlog() should order exclusivity tasks before non-exclusivity tasks for supervisors."""
        with time_machine.travel("2024-01-01 00:00:00", tick=False) as traveller:
            # Create a task in exclusivity period
            task_in_exclusivity = IdentificationTaskFactory(
                report__point=country.geom.point_on_surface, report__country=country
            )

            # Create a task outside exclusivity period
            traveller.shift(
                timedelta(days=country.workspace.supervisor_exclusivity_days + 1)
            )

            task_outside_exclusivity = IdentificationTaskFactory(
                report__point=country.geom.point_on_surface, report__country=country
            )

        result = list(IdentificationTask.objects.backlog(user=user_national_supervisor))

        assert len(result) == 2
        # Exclusivity tasks should come first
        assert result[0] == task_in_exclusivity
        assert result[1] == task_outside_exclusivity

    def test_backlog_nuts2_has_higher_priority_than_workspace(self):
        """backlog() should prioritize NUTS2 tasks over general workspace tasks."""
        user = UserFactory()

        workspace = WorkspaceFactory()
        WorkspaceMembership.objects.create(
            workspace=workspace, user=user, role=WorkspaceMembership.Role.ANNOTATOR
        )

        # Create another workspace in the same country for testing
        other_workspace = WorkspaceFactory()
        WorkspaceMembership.objects.create(
            workspace=other_workspace,
            user=user,
            role=WorkspaceMembership.Role.ANNOTATOR,
        )

        # Setup NUTS2 in first workspace
        nuts2_region = NutsEuropeFactory(
            levl_code=2, europecountry=workspace.country, geom=workspace.country.geom
        )
        user.userstat.nuts2_assignation = nuts2_region
        user.userstat.save()

        # Create tasks
        task_nuts2 = IdentificationTaskFactory(
            report__point=nuts2_region.geom.point_on_surface,
            report__country=workspace.country,
        )

        task_other_workspace = IdentificationTaskFactory(
            report__point=other_workspace.country.geom.point_on_surface,
            report__country=other_workspace.country,
        )

        result = list(IdentificationTask.objects.backlog(user=user))

        # NUTS2 task should come before other workspace task
        assert result.index(task_nuts2) < result.index(task_other_workspace)

    # Test browsable() method
    def test_browsable_returns_all_for_user_with_view_perm(self, identification_task):
        """browsable() should return all tasks for users with view permission."""
        user_with_perm = UserFactory()
        from django.contrib.contenttypes.models import ContentType
        from django.contrib.auth.models import Permission

        content_type = ContentType.objects.get_for_model(IdentificationTask)
        permission = Permission.objects.get(
            codename="view_identificationtask", content_type=content_type
        )
        user_with_perm.user_permissions.add(permission)

        result = IdentificationTask.objects.browsable(user=user_with_perm)

        assert result.count() == 1

    def test_browsable_excludes_archived_without_perm(self, identification_task, user):
        """browsable() should exclude archived tasks for users without permission."""
        identification_task.status = IdentificationTask.Status.ARCHIVED
        identification_task.save()

        result = IdentificationTask.objects.browsable(user=user)

        assert result.count() == 0

    def test_browsable_returns_user_annotated_tasks(self, identification_task, user):
        """browsable() should return tasks annotated by the user."""
        ExpertReportAnnotationFactory(
            identification_task=identification_task, user=user, is_finished=True
        )

        result = IdentificationTask.objects.browsable(user=user)

        assert result.count() == 1

    def test_browsable_excludes_other_users_tasks(self, identification_task, user):
        """browsable() should exclude tasks not annotated by user without permissions."""
        result = IdentificationTask.objects.browsable(user=user)

        assert result.count() == 0


@pytest.mark.django_db
class TestIdentificationTaskFlow:
    def _add_annotation(
        self,
        identification_task: IdentificationTask,
        is_finished: bool = True,
        **kwargs,
    ) -> ExpertReportAnnotation:
        user_expert = User.objects.create(username=str(uuid.uuid4()))

        return ExpertReportAnnotation.objects.create(
            identification_task=identification_task,
            user=user_expert,
            is_finished=is_finished,
            **kwargs,
        )

    def _add_review(
        self,
        identification_task: IdentificationTask,
        overwrite: bool = False,
        is_finished: bool = True,
        **kwargs,
    ) -> ExpertReportAnnotation:
        user_expert = User.objects.create(username=str(uuid.uuid4()))

        if not overwrite:
            identification_task.review_type = IdentificationTask.Review.AGREE
            identification_task.reviewed_at = timezone.now()
            identification_task.reviewed_by = user_expert
            identification_task.save()
        else:
            return ExpertReportAnnotation.objects.create(
                identification_task=identification_task,
                user=user_expert,
                decision_level=ExpertReportAnnotation.DecisionLevel.FINAL,
                is_finished=is_finished,
                **kwargs,
            )

    # triggers from Report
    def test_identification_task_is_created_on_adult_report_creation_with_photos(
        self, adult_report
    ):
        identification_task_qs = IdentificationTask.objects.filter(report=adult_report)
        assert identification_task_qs.count() == 0

        # Creating photo for the report
        _ = Photo.objects.create(report=adult_report, photo="./testdata/splash.png")
        assert identification_task_qs.count() == 1

    def test_identification_task_status_should_be_archive_after_report_is_hidden(
        self, identification_task
    ):
        assert identification_task.status == IdentificationTask.Status.OPEN

        report = identification_task.report
        report.hide = True
        report.save()

        identification_task.refresh_from_db()
        assert identification_task.status == IdentificationTask.Status.ARCHIVED

    def test_identification_task_status_should_be_archive_if_report_has_tag_345(
        self, identification_task
    ):
        assert identification_task.status == IdentificationTask.Status.OPEN

        report = identification_task.report
        report.tags.add("345")
        report.save()

        identification_task.refresh_from_db()
        assert identification_task.status == IdentificationTask.Status.ARCHIVED

    def test_identification_task_status_should_be_archive_after_report_is_soft_deleted(
        self, identification_task
    ):
        assert identification_task.status == IdentificationTask.Status.OPEN

        report = identification_task.report
        report.soft_delete()

        identification_task.refresh_from_db()
        assert identification_task.status == IdentificationTask.Status.ARCHIVED

        report.restore()
        identification_task.refresh_from_db()
        assert identification_task.status != IdentificationTask.Status.ARCHIVED

    def test_identification_task_status_should_be_deleted_after_report_deletion(
        self, identification_task
    ):
        assert identification_task.status == IdentificationTask.Status.OPEN

        report = identification_task.report
        report.delete()

        assert IdentificationTask.objects.filter(pk=identification_task.pk).count() == 0

    # manager
    def test_objects_new_return_never_assigned_tasks(self, identification_task):
        assert identification_task.status == IdentificationTask.Status.OPEN
        assert identification_task.assignees.count() == 0

        assert frozenset(IdentificationTask.objects.new()) == frozenset(
            [identification_task]
        )

    def test_objects_ongoing(self, identification_task):
        assert identification_task.status == IdentificationTask.Status.OPEN
        assert identification_task.assignees.count() == 0

        self._add_annotation(identification_task=identification_task)

        assert frozenset(IdentificationTask.objects.ongoing()) == frozenset(
            [identification_task]
        )

    def test_objects_blocked(self, identification_task):
        assert identification_task.status == IdentificationTask.Status.OPEN
        assert identification_task.assignees.count() == 0

        with time_machine.travel("2024-01-01 00:00:00", tick=False) as traveller:
            self._add_annotation(
                identification_task=identification_task, is_finished=False
            )

            traveller.shift(timedelta(days=15))

            # Still assignable, not blocked yet.
            assert IdentificationTask.objects.blocked(days=15).count() == 0

            self._add_annotation(
                identification_task=identification_task, is_finished=True
            )
            self._add_annotation(
                identification_task=identification_task, is_finished=True
            )

            # Now it's blocked. Fully assigned but the only missing annotations is not complete.
            assert frozenset(IdentificationTask.objects.blocked(days=15)) == frozenset(
                [identification_task]
            )

    def test_objects_annotating(self, identification_task):
        assert identification_task.status == IdentificationTask.Status.OPEN
        assert identification_task.assignees.count() == 0

        annotation = self._add_annotation(
            identification_task=identification_task, is_finished=False
        )

        assert frozenset(IdentificationTask.objects.annotating()) == frozenset(
            [identification_task]
        )

        annotation.is_finished = True
        annotation.save()

        assert IdentificationTask.objects.annotating().count() == 0

    def test_objects_to_review(self, identification_task):
        assert identification_task.status == IdentificationTask.Status.OPEN
        assert identification_task.assignees.count() == 0

        for _ in range(settings.MAX_N_OF_EXPERTS_ASSIGNED_PER_REPORT):  # noqa: F402
            self._add_annotation(identification_task=identification_task)

        assert frozenset(IdentificationTask.objects.to_review()) == frozenset(
            [identification_task]
        )

    @pytest.mark.parametrize("status_value", IdentificationTask.CLOSED_STATUS)
    def test_objects_closed(self, identification_task, status_value):
        identification_task.status = status_value
        identification_task.save()
        assert frozenset(IdentificationTask.objects.closed()) == frozenset(
            [identification_task]
        )

    @pytest.mark.parametrize("is_overwrite", [True, False])
    def test_objects_done(self, identification_task, is_overwrite):
        assert identification_task.status == IdentificationTask.Status.OPEN
        assert identification_task.assignees.count() == 0

        for _ in range(settings.MAX_N_OF_EXPERTS_ASSIGNED_PER_REPORT):  # noqa: F402
            self._add_annotation(identification_task=identification_task)

        self._add_review(
            identification_task=identification_task, overwrite=is_overwrite
        )

        identification_task.refresh_from_db()

        assert frozenset(IdentificationTask.objects.done()) == frozenset(
            [identification_task]
        )

    # counters
    @pytest.mark.parametrize(
        "is_finished, expected_result",
        [
            (True, 1),
            (False, 1),
        ],
    )
    def test_total_annotations_should_be_increased_on_new_annotation(
        self, identification_task, is_finished, expected_result
    ):
        assert identification_task.total_annotations == 0

        _ = self._add_annotation(
            identification_task=identification_task, is_finished=is_finished
        )

        identification_task.refresh_from_db()
        assert identification_task.total_annotations == expected_result

    def test_total_annotation_counters_should_not_be_increased_if_superexpert(
        self, identification_task
    ):
        assert identification_task.total_annotations == 0
        assert identification_task.total_finished_annotations == 0

        self._add_review(identification_task=identification_task, overwrite=False)

        identification_task.refresh_from_db()
        assert identification_task.total_annotations == 0
        assert identification_task.total_finished_annotations == 0

    @pytest.mark.parametrize(
        "is_finished, expected_result",
        [
            (True, 1),
            (False, 0),
        ],
    )
    def test_total_finished_annotations_should_be_increased_on_new_annotation(
        self, identification_task, is_finished, expected_result
    ):
        assert identification_task.total_finished_annotations == 0

        self._add_annotation(
            identification_task=identification_task, is_finished=is_finished
        )

        identification_task.refresh_from_db()
        assert identification_task.total_finished_annotations == expected_result

    # assignees many2many relationship
    def test_assignees(self, identification_task):
        assert identification_task.assignees.count() == 0

        _ = self._add_annotation(identification_task=identification_task)
        assert identification_task.assignees.count() == 1

        self._add_review(identification_task=identification_task, overwrite=False)
        assert identification_task.assignees.count() == 1

        self._add_review(identification_task=identification_task, overwrite=True)
        assert identification_task.assignees.count() == 2

    # status field transition
    @pytest.mark.parametrize(
        "num_is_relevant, expected_result",
        [
            (0, False),
            (1, True),
            (2, True),
            (3, True),
        ],
    )
    def test_status_should_be_conflict(
        self, identification_task, taxon_root, num_is_relevant, expected_result
    ):
        genus = taxon_root.add_child(name="genus", rank=Taxon.TaxonomicRank.GENUS)

        taxa = []
        for i in range(settings.MAX_N_OF_EXPERTS_ASSIGNED_PER_REPORT):
            t = genus.add_child(
                name="specie {}".format(i),
                rank=Taxon.TaxonomicRank.SPECIES,
                is_relevant=i < num_is_relevant,
            )
            taxa.append(t)

        for taxon in taxa:
            self._add_annotation(
                identification_task=identification_task,
                taxon=taxon,
                confidence=ExpertReportAnnotation.ConfidenceCategory.DEFINITELY,
                status=ExpertReportAnnotation.Status.PUBLIC,
            )

        identification_task.refresh_from_db()

        assert (
            identification_task.status == IdentificationTask.Status.CONFLICT
        ) == expected_result
        assert identification_task.is_flagged == expected_result

    def test_should_be_flagged(self, identification_task, taxon_root):
        genus = taxon_root.add_child(name="genus", rank=Taxon.TaxonomicRank.GENUS)
        specie_1 = genus.add_child(name="specie 1", rank=Taxon.TaxonomicRank.SPECIES)
        _ = genus.add_child(name="specie 2", rank=Taxon.TaxonomicRank.SPECIES)

        for _ in range(settings.MAX_N_OF_EXPERTS_ASSIGNED_PER_REPORT - 1):
            self._add_annotation(
                identification_task=identification_task,
                taxon=specie_1,
                confidence=ExpertReportAnnotation.ConfidenceCategory.DEFINITELY,
                status=ExpertReportAnnotation.Status.PUBLIC,
            )

        # Mark as flagged
        self._add_annotation(
            identification_task=identification_task,
            taxon=specie_1,
            confidence=ExpertReportAnnotation.ConfidenceCategory.DEFINITELY,
            status=ExpertReportAnnotation.Status.FLAGGED,
        )

        identification_task.refresh_from_db()

        assert identification_task.status == IdentificationTask.Status.REVIEW
        assert identification_task.is_flagged

        self._add_review(identification_task=identification_task)

        identification_task.refresh_from_db()
        assert identification_task.status == IdentificationTask.Status.DONE
        assert not identification_task.is_flagged

    def test_one_flagged_annotation_sets_status_to_review(self, identification_task):
        # Mark as flagged
        self._add_annotation(
            identification_task=identification_task,
            status=ExpertReportAnnotation.Status.FLAGGED,
        )

        identification_task.refresh_from_db()
        assert identification_task.status == IdentificationTask.Status.REVIEW
        assert identification_task.is_flagged

    # overview general
    @pytest.mark.parametrize("overwrite", [False, True])
    def test_fields_are_overwriten_on_review(
        self, identification_task, taxon_root, overwrite
    ):
        genus = taxon_root.add_child(name="genus", rank=Taxon.TaxonomicRank.GENUS)
        specie_1 = genus.add_child(name="specie 1", rank=Taxon.TaxonomicRank.SPECIES)
        specie_2 = genus.add_child(name="specie 2", rank=Taxon.TaxonomicRank.SPECIES)

        first_photo = identification_task.report.photos.first()
        another_photo = Photo.objects.create(
            report=identification_task.report, photo="./testdata/splash.png"
        )

        for _ in range(settings.MAX_N_OF_EXPERTS_ASSIGNED_PER_REPORT - 1):  # noqa: F402
            self._add_annotation(
                identification_task=identification_task,
                taxon=specie_1,
                confidence=ExpertReportAnnotation.ConfidenceCategory.DEFINITELY,
                status=ExpertReportAnnotation.Status.PUBLIC,
                public_note="public message",
                message_for_user="message to user",
                best_photo=another_photo,
            )

        # Disagree with others
        self._add_annotation(
            identification_task=identification_task,
            taxon=specie_2,
            confidence=ExpertReportAnnotation.ConfidenceCategory.PROBABLY,
            status=ExpertReportAnnotation.Status.PUBLIC,
            public_note="random public message",
            message_for_user="random message to user",
            best_photo=another_photo,
        )

        identification_task.refresh_from_db()

        assert identification_task.photo == another_photo
        assert identification_task.public_note == "public message"
        assert (
            identification_task.message_for_user is None
        )  # Only superexperts and national supervisor can.
        assert identification_task.taxon == specie_1
        assert identification_task.confidence == Decimal("0.75")  # (1 + 1 + 0.25) / 3
        assert identification_task.agreement == 2 / 3
        assert identification_task.is_safe
        assert not identification_task.is_flagged
        assert identification_task.status == IdentificationTask.Status.DONE

        self._add_review(
            identification_task=identification_task,
            overwrite=overwrite,
            taxon=specie_2,
            confidence=ExpertReportAnnotation.ConfidenceCategory.DEFINITELY,
            status=ExpertReportAnnotation.Status.HIDDEN,
            public_note="new public message",
            message_for_user="new message to user",
            best_photo=first_photo,
        )

        identification_task.refresh_from_db()

        if overwrite:
            assert identification_task.photo == first_photo
            assert identification_task.public_note == "new public message"
            assert identification_task.message_for_user == "new message to user"
            assert identification_task.taxon == specie_2
            assert identification_task.confidence == Decimal("1")
            assert identification_task.agreement == 1
            assert not identification_task.is_safe  # NOTE: superexpert has overwritten
            assert not identification_task.is_flagged
            assert identification_task.status == IdentificationTask.Status.DONE

            annotation_review = ExpertReportAnnotation.objects.get(
                identification_task=identification_task,
                decision_level=ExpertReportAnnotation.DecisionLevel.FINAL,
            )
            # Change to FLAGGED
            annotation_review.status = ExpertReportAnnotation.Status.FLAGGED
            annotation_review.save()

            identification_task.refresh_from_db()

            assert identification_task.is_safe
            assert identification_task.is_flagged
        else:
            # From expert consensus
            assert identification_task.photo == another_photo
            assert identification_task.public_note == "public message"
            assert (
                identification_task.message_for_user is None
            )  # Only superexperts and national supervisor can.
            assert identification_task.taxon == specie_1
            assert identification_task.confidence == Decimal(
                "0.75"
            )  # (1 + 1 + 0.25) / 3
            assert identification_task.agreement == 2 / 3
            assert identification_task.is_safe  # NOTE: now is reviewed
            assert not identification_task.is_flagged
            assert identification_task.status == IdentificationTask.Status.DONE

    def test_executive_annotation(self, identification_task, taxon_root):
        genus = taxon_root.add_child(name="genus", rank=Taxon.TaxonomicRank.GENUS)
        specie_1 = genus.add_child(name="specie 1", rank=Taxon.TaxonomicRank.SPECIES)
        _ = genus.add_child(name="specie 2", rank=Taxon.TaxonomicRank.SPECIES)

        _ = identification_task.report.photos.first()
        another_photo = Photo.objects.create(
            report=identification_task.report, photo="./testdata/splash.png"
        )

        # Executive annotation
        annotation = self._add_annotation(
            identification_task=identification_task,
            taxon=specie_1,
            confidence=ExpertReportAnnotation.ConfidenceCategory.PROBABLY,
            status=ExpertReportAnnotation.Status.PUBLIC,
            public_note="public message",
            message_for_user="message to user",
            best_photo=another_photo,
            decision_level=ExpertReportAnnotation.DecisionLevel.EXECUTIVE,
        )

        identification_task.refresh_from_db()

        assert identification_task.photo == another_photo
        assert identification_task.public_note == "public message"
        assert (
            identification_task.message_for_user == "message to user"
        )  # Only national supervisor can validate executive.
        assert identification_task.taxon == specie_1
        assert identification_task.confidence == Decimal("0.75")
        assert identification_task.agreement == 1
        assert identification_task.is_safe
        assert identification_task.status == IdentificationTask.Status.DONE
        assert not identification_task.is_flagged

        # Now change to flagged
        annotation.status = ExpertReportAnnotation.Status.FLAGGED
        annotation.save()

        identification_task.refresh_from_db()
        assert identification_task.is_safe
        assert identification_task.status == IdentificationTask.Status.REVIEW
        assert identification_task.is_flagged

    # review field transition
    @pytest.mark.parametrize("overwrite", [False, True])
    @time_machine.travel("2024-01-01 00:00:00", tick=False)
    def test_reviewed_at_is_set_after_review(self, identification_task, overwrite):
        assert not identification_task.is_reviewed
        assert identification_task.reviewed_by is None

        self._add_review(identification_task=identification_task, overwrite=overwrite)

        identification_task.refresh_from_db()

        assert identification_task.is_reviewed
        assert identification_task.reviewed_at == timezone.now()
        assert identification_task.reviewed_by is not None

    @pytest.mark.parametrize(
        "overwrite, expected_result",
        [
            (False, IdentificationTask.Review.AGREE),
            (True, IdentificationTask.Review.OVERWRITE),
        ],
    )
    def test_review_type_is_set_after_review(
        self, identification_task, overwrite, expected_result
    ):
        assert not identification_task.is_reviewed

        self._add_review(identification_task=identification_task, overwrite=overwrite)

        identification_task.refresh_from_db()

        assert identification_task.is_reviewed
        assert identification_task.review_type == expected_result

    # lifecycle triggers
    @pytest.mark.parametrize(
        "status, is_safe, should_publish",
        [
            (IdentificationTask.Status.DONE, True, True),
            (IdentificationTask.Status.DONE, False, False),
            (IdentificationTask.Status.ARCHIVED, True, False),
            (IdentificationTask.Status.ARCHIVED, False, False),
            (IdentificationTask.Status.OPEN, True, False),
            (IdentificationTask.Status.OPEN, False, False),
            (IdentificationTask.Status.REVIEW, True, False),
            (IdentificationTask.Status.REVIEW, False, False),
        ],
    )
    @time_machine.travel("2024-01-01 00:00:00", tick=False)
    def test_on_status_change_sets_report_published_at(
        self, identification_task, status, is_safe, should_publish
    ):
        assert not identification_task.report.published

        identification_task.status = status
        identification_task.save()

        assert not identification_task.report.published

        identification_task.is_safe = is_safe
        identification_task.save()

        identification_task.report.refresh_from_db()

        assert identification_task.report.published == should_publish
        if should_publish:
            assert identification_task.report.published_at == timezone.now()
        else:
            assert identification_task.report.published_at is None

    @pytest.mark.parametrize(
        "result_source, creates_notification",
        [
            (IdentificationTask.ResultSource.EXPERT, True),
            (IdentificationTask.ResultSource.AI, False),
        ],
    )
    def test_on_status_done_notification_is_sent(
        self, identification_task, result_source, creates_notification
    ):
        identification_task.result_source = result_source
        identification_task.status = IdentificationTask.Status.DONE
        identification_task.save()

        notification_qs = Notification.objects.filter(
            recipients=identification_task.report.user,
            report=identification_task.report,
        )

        assert notification_qs.exists() == creates_notification
        if creates_notification:
            notification = notification_qs.first()
            assert notification.notification_content.title == _(
                "your_picture_has_been_validated_by_an_expert"
            )
