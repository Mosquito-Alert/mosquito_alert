from abc import ABC

from mosquito_alert.utils.tests.test_models import AbstractDjangoModelTestMixin

##########################
# Identifier Profile
##########################


class BaseTestIdentifierProfile(AbstractDjangoModelTestMixin, ABC):
    # fields
    def test_is_identifier_can_not_be_null(self):
        assert not self.model._meta.get_field("is_identifier").null

    def test_is_identifier_is_default_False(self):
        assert not self.model._meta.get_field("is_identifier").default

    def test_is_superidentifier_can_not_be_null(self):
        assert not self.model._meta.get_field("is_superidentifier").null

    def test_is_superidentifier_is_default_False(self):
        assert not self.model._meta.get_field("is_superidentifier").default
