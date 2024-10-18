import pytest
from django.db import models
from django.db.utils import IntegrityError

from mosquito_alert.utils.tests.test_models import BaseTestTimeStampedModel

from ..models import BoundaryAuthorization, BoundaryMembership
from .factories import BoundaryAuthorizationFactory, BoundaryMembershipFactory


@pytest.mark.django_db
class TestBoundaryAuthorizationModel(BaseTestTimeStampedModel):
    model = BoundaryAuthorization
    factory_cls = BoundaryAuthorizationFactory

    # fields
    def test_boundary_can_not_be_null(self):
        assert not self.model._meta.get_field("boundary").null

    def test_boundary_deletion_is_cascaded(self):
        _on_delete = self.model._meta.get_field("boundary").remote_field.on_delete
        assert _on_delete == models.CASCADE

    def test_supervisor_exclusivity_days_can_not_be_null(self):
        assert not self.model._meta.get_field("supervisor_exclusivity_days").null

    def test_supervisor_exclusivity_days_must_be_postive_integer(self):
        with pytest.raises(IntegrityError):
            _ = self.factory_cls(supervisor_exclusivity_days=-1)

    def test_supervisor_exclusivity_days_default_to_15_days(self):
        assert self.model._meta.get_field("supervisor_exclusivity_days").default == 15

    def test_members_only_can_not_be_null(self):
        assert not self.model._meta.get_field("members_only").null

    def test_members_only_default_to_False(self):
        assert not self.model._meta.get_field("members_only").default

    # meta


@pytest.mark.django_db
class TestBoundaryMembershipModel(BaseTestTimeStampedModel):
    model = BoundaryMembership
    factory_cls = BoundaryMembershipFactory

    # fields
    def test_boundary_authorization_can_not_be_null(self):
        assert not self.model._meta.get_field("boundary_authorization").null

    def test_boundary_authorization_deletion_is_cascaded(self):
        _on_delete = self.model._meta.get_field("boundary_authorization").remote_field.on_delete
        assert _on_delete == models.CASCADE

    def test_user_can_not_be_null(self):
        assert not self.model._meta.get_field("user").null

    def test_user_deletion_is_cascaded(self):
        _on_delete = self.model._meta.get_field("user").remote_field.on_delete
        assert _on_delete == models.CASCADE

    def test_role_can_not_be_null(self):
        assert not self.model._meta.get_field("role").null

    # meta
