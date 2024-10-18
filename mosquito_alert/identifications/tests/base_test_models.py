from abc import ABC

from django.db import models

from mosquito_alert.utils.tests.test_models import AbstractDjangoModelTestMixin

##########################
# Identifier Profile
##########################


class BaseTestIdentifierProfile(AbstractDjangoModelTestMixin, ABC):
    # fields
    def test_preferred_identification_boundary_can_be_null(self):
        assert self.model._meta.get_field("preferred_identification_boundary").null

    def test_preferred_identification_boundary_can_be_blank(self):
        assert self.model._meta.get_field("preferred_identification_boundary").blank

    def test_preferred_identification_boundary_deletion_is_setnull(self):
        _on_delete = self.model._meta.get_field("preferred_identification_boundary").remote_field.on_delete
        assert _on_delete == models.SET_NULL

    def test_is_identifier_can_not_be_null(self):
        assert not self.model._meta.get_field("is_identifier").null

    def test_is_identifier_is_default_False(self):
        assert not self.model._meta.get_field("is_identifier").default

    def test_is_superidentifier_can_not_be_null(self):
        assert not self.model._meta.get_field("is_superidentifier").null

    def test_is_superidentifier_is_default_False(self):
        assert not self.model._meta.get_field("is_superidentifier").default
