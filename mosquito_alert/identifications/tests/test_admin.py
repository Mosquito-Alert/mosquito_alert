from unittest.mock import Mock, patch

import pytest
from django.contrib.admin.sites import AdminSite
from django.urls import reverse

from ..admin import (
    ExternalIdentificationAdminInline,
    IdentifierProfileAdmin,
    IndividualIdentificationTaskAdmin,
    IndividualIdentificationTaskResultAdmin,
    IndividualIdentificationTaskResultAdminInline,
    PhotoIdentificationTaskAdmin,
    PhotoIdentificationTaskAdminInline,
    PhotoIdentificationTaskResultAdmin,
    PhotoIdentificationTaskResultAdminInline,
    PredictionAdminInline,
    TaxonClassificationCandidateAdminInline,
    UserIdentificationAdminInline,
)
from ..forms import TaxonClassificationCandidateForm, TaxonClassificationCategorizedProbabilityCandidateForm
from ..formsets import TaxonClassificationCandidateFormSet
from ..models import (
    IdentifierProfile,
    IndividualIdentificationTask,
    IndividualIdentificationTaskResult,
    PhotoIdentificationTask,
    PhotoIdentificationTaskResult,
)
from .factories import (
    IdentifierProfileFactory,
    IndividualIdentificationTaskFactory,
    IndividualIdentificationTaskResultFactory,
    PhotoIdentificationTaskFactory,
    PhotoIdentificationTaskResultFactory,
    TaxonClassificationCandidateFactory,
    UserIdentificationFactory,
)
from .models import DummyBaseClassification

############################
# admin.ModelAdmin tests
############################


class TestidentifierprofileAdmin:
    @pytest.mark.parametrize("fieldname", ["user__name", "user__username"])
    def test_can_search_by(self, fieldname):
        assert fieldname in IdentifierProfileAdmin.search_fields

    def test_user_field_is_autocomplete(self):
        assert "user" in IdentifierProfileAdmin.autocomplete_fields

    @pytest.mark.django_db
    def test_user_field_is_readonly_on_change(self, admin_user):
        assert "user" in IdentifierProfileAdmin(model=IdentifierProfile, admin_site=AdminSite()).get_readonly_fields(
            request=Mock(user=admin_user), obj=IdentifierProfileFactory()
        )

    @pytest.mark.parametrize("fieldname", ["is_superexpert", "is_active", "created_at", "updated_at"])
    def test_list_filter(self, admin_user, fieldname):
        list_filter = IdentifierProfileAdmin(model=IdentifierProfile, admin_site=AdminSite()).get_list_filter(
            request=Mock(user=admin_user)
        )

        fields = [x if not isinstance(x, tuple) else x[0] for x in list_filter]

        assert fieldname in fields

    def test_add(self, admin_client, user):
        url = reverse("admin:identifications_identifierprofile_add")
        response = admin_client.get(url)
        assert response.status_code == 200

        response = admin_client.post(
            url,
            data={"user": user.pk, "is_superexpert": "1"},
        )
        assert response.status_code == 302
        instance = IdentifierProfile.objects.get(user=user)

        assert instance.pk == user.pk
        assert instance.is_superexpert is True

    def test_view(self, admin_client):
        bite = IdentifierProfileFactory()
        url = reverse(
            "admin:identifications_identifierprofile_change",
            kwargs={"object_id": bite.pk},
        )
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_changelist(self, admin_client):
        url = reverse("admin:identifications_identifierprofile_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200


class TestIndividualIdentificationTaskResultAdmin:
    @pytest.mark.parametrize("fieldname", ["type", "sex", "label", "probability", "created_at", "updated_at"])
    def test_list_filter(self, fieldname, admin_user):
        list_filter = IndividualIdentificationTaskResultAdmin(
            model=IndividualIdentificationTaskResult, admin_site=AdminSite()
        ).get_list_filter(request=Mock(user=admin_user))

        fields = [x if not isinstance(x, tuple) else x[0] for x in list_filter]

        assert fieldname in fields

    def test_add_is_not_allowed(self, admin_client):
        url = reverse("admin:identifications_individualidentificationtaskresult_add")
        response = admin_client.get(url)
        assert response.status_code == 403

    def test_view(self, admin_client):
        i_t_result = IndividualIdentificationTaskResultFactory()
        url = reverse(
            "admin:identifications_individualidentificationtaskresult_change",
            kwargs={"object_id": i_t_result.pk},
        )
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_changelist(self, admin_client):
        url = reverse("admin:identifications_individualidentificationtaskresult_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200


class TestIndividualIdentificationTaskAdmin:
    @pytest.mark.parametrize("fieldname", ["is_locked", "is_completed", "created_at", "updated_at"])
    def test_list_filter(self, fieldname, admin_user):
        list_filter = IndividualIdentificationTaskAdmin(
            model=IndividualIdentificationTask, admin_site=AdminSite()
        ).get_list_filter(request=Mock(user=admin_user))

        fields = [x if not isinstance(x, tuple) else x[0] for x in list_filter]

        assert fieldname in fields

    @pytest.mark.parametrize(
        "inline_class", [IndividualIdentificationTaskResultAdminInline, PhotoIdentificationTaskAdminInline]
    )
    def test_inlines(self, inline_class):
        assert inline_class in IndividualIdentificationTaskAdmin.inlines

    def test_add_is_not_allowed(self, admin_client):
        url = reverse("admin:identifications_individualidentificationtask_add")
        response = admin_client.get(url)
        assert response.status_code == 403

    def test_view(self, admin_client):
        i_t_result = IndividualIdentificationTaskFactory()
        url = reverse(
            "admin:identifications_individualidentificationtask_change",
            kwargs={"object_id": i_t_result.pk},
        )
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_changelist(self, admin_client):
        url = reverse("admin:identifications_individualidentificationtask_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200


class TestPhotoIdentificationTaskResultAdmin:
    @pytest.mark.parametrize(
        "fieldname", ["is_ground_truth", "type", "sex", "label", "probability", "created_at", "updated_at"]
    )
    def test_list_filter(self, fieldname, admin_user):
        list_filter = PhotoIdentificationTaskResultAdmin(
            model=PhotoIdentificationTaskResult, admin_site=AdminSite()
        ).get_list_filter(request=Mock(user=admin_user))

        fields = [x if not isinstance(x, tuple) else x[0] for x in list_filter]

        assert fieldname in fields

    def test_add_is_not_allowed(self, admin_client):
        url = reverse("admin:identifications_photoidentificationtaskresult_add")
        response = admin_client.get(url)
        assert response.status_code == 403

    def test_view(self, admin_client):
        i_t_result = PhotoIdentificationTaskResultFactory()
        url = reverse(
            "admin:identifications_photoidentificationtaskresult_change",
            kwargs={"object_id": i_t_result.pk},
        )
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_changelist(self, admin_client):
        url = reverse("admin:identifications_photoidentificationtaskresult_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200


class TestPhotoIdentificationTaskAdmin:
    @pytest.mark.parametrize(
        "fieldname",
        [
            "total_annotations",
            "skipped_annotations",
            "total_predictions",
            "total_external",
            "is_completed",
            "created_at",
            "updated_at",
        ],
    )
    def test_list_filter(self, fieldname, admin_user):
        list_filter = PhotoIdentificationTaskAdmin(
            model=PhotoIdentificationTask, admin_site=AdminSite()
        ).get_list_filter(request=Mock(user=admin_user))

        fields = [x if not isinstance(x, tuple) else x[0] for x in list_filter]

        assert fieldname in fields

    def test_search_by_photo_image_name(self):
        assert "photo__image" in PhotoIdentificationTaskAdmin.search_fields

    @pytest.mark.parametrize(
        "inline_class",
        [
            PhotoIdentificationTaskResultAdminInline,
            UserIdentificationAdminInline,
            PredictionAdminInline,
            ExternalIdentificationAdminInline,
        ],
    )
    def test_inlines(self, inline_class):
        assert inline_class in PhotoIdentificationTaskAdmin.inlines

    def test_add_is_not_allowed(self, admin_client):
        url = reverse("admin:identifications_photoidentificationtask_add")
        response = admin_client.get(url)
        assert response.status_code == 403

    def test_view(self, admin_client):
        i_t_result = PhotoIdentificationTaskFactory()
        url = reverse(
            "admin:identifications_photoidentificationtask_change",
            kwargs={"object_id": i_t_result.pk},
        )
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_changelist(self, admin_client):
        url = reverse("admin:identifications_photoidentificationtask_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_only_recompute_is_called_once_on_change(self, admin_user):
        dummy_request = Mock(user=admin_user, POST=[])

        task = PhotoIdentificationTaskFactory()
        ui = UserIdentificationFactory(task=task)
        _ = TaxonClassificationCandidateFactory(content_object=ui, is_seed=True, probability=1)
        ui2 = UserIdentificationFactory(task=task)
        _ = TaxonClassificationCandidateFactory(content_object=ui2, is_seed=True, probability=1)

        admin = PhotoIdentificationTaskAdmin(model=PhotoIdentificationTask, admin_site=AdminSite())
        formsets, _ = admin._create_formsets(request=dummy_request, obj=task, change=False)

        # TODO: formsets do not include TaxonCandidate formsets.
        form = Mock()
        form.instance = task

        with patch("django.forms.forms.BaseForm.has_changed", return_value=True):
            with patch.object(task, "update_results", return_value=True) as mocked_method:
                admin.save_related(request=dummy_request, form=form, formsets=reversed(formsets), change=False)

                mocked_method.assert_called_once()


############################
# inline tests
############################


class TestTaxonClassificationCandidateAdminInline:
    def test_form(self):
        assert TaxonClassificationCandidateAdminInline.form == TaxonClassificationCandidateForm

    def test_formset(self):
        assert TaxonClassificationCandidateAdminInline.formset == TaxonClassificationCandidateFormSet

    @pytest.mark.django_db
    def test_get_queryset_only_shows_seeds(self, admin_user):
        admin = TaxonClassificationCandidateAdminInline(parent_model=DummyBaseClassification, admin_site=AdminSite())

        t_seed = TaxonClassificationCandidateFactory(is_seed=True)
        _ = TaxonClassificationCandidateFactory(is_seed=False)

        assert list(admin.get_queryset(request=Mock(user=admin_user)).all()) == [t_seed]


class TestUserIdentificationAdminInline:
    def test_inline_form_is_TaxonClassificationCategorizedProbabilityCandidateForm(self):
        assert all(
            map(
                lambda x: x.form == TaxonClassificationCategorizedProbabilityCandidateForm,
                filter(
                    lambda x: isinstance(x, TaxonClassificationCandidateAdminInline),
                    UserIdentificationAdminInline.inlines,
                ),
            )
        )
