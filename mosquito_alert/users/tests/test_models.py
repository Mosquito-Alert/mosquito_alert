import pytest
from django.db import models

from mosquito_alert.identifications.tests.base_test_models import BaseTestIdentifierProfile
from mosquito_alert.users.models import User, UserProfile

from .factories import UserFactory


def test_user_get_absolute_url(user: User):
    assert user.get_absolute_url() == f"/users/{user.username}/"


@pytest.mark.django_db
class TestUser:
    def test_user_profile_is_created_on_new_user(self):
        obj = UserFactory()

        assert obj.profile


@pytest.mark.django_db
class TestUserProfile(BaseTestIdentifierProfile):
    model = UserProfile
    factory_cls = None

    # fields
    def test_user_can_not_be_null(self):
        assert not self.model._meta.get_field("user").null

    def test_user_is_pk(self):
        assert self.model._meta.get_field("user").primary_key

    def test_cascade_user_on_delete(self):
        _on_delete = self.model._meta.get_field("user").remote_field.on_delete
        assert _on_delete == models.CASCADE

    def test_user_related_name_is_profile(self):
        assert self.model._meta.get_field("user").remote_field.related_name == "profile"
